import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied

from .models import NameGroup, NameVariant, NamingGroup, GroupMembership, Swipe, Score
from .forms import SignupForm, NamingGroupForm


def index(request):
    if request.user.is_authenticated:
        return redirect('swipe')
    return redirect('login')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('swipe')
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('swipe')
    else:
        form = SignupForm()
    return render(request, 'auth/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('swipe')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', '')
            return redirect(next_url or 'swipe')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'auth/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def group_list(request):
    groups = request.user.naming_groups.all().order_by('-created_at')
    return render(request, 'groups/list.html', {'groups': groups})


@login_required
def group_create(request):
    if request.method == 'POST':
        form = NamingGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.owner = request.user
            group.save()
            GroupMembership.objects.create(user=request.user, group=group)
            messages.success(request, f'Group "{group.name}" created!')
            return redirect('group_detail', pk=group.pk)
    else:
        form = NamingGroupForm()
    return render(request, 'groups/create.html', {'form': form})


@login_required
def group_detail(request, pk):
    group = get_object_or_404(NamingGroup, pk=pk)
    if not group.members.filter(id=request.user.id).exists():
        raise PermissionDenied
    invite_url = request.build_absolute_uri(f'/invite/{group.invite_token}/')
    members = group.members.all()
    return render(request, 'groups/detail.html', {
        'group': group,
        'invite_url': invite_url,
        'members': members,
    })


@login_required
@require_POST
def remove_member(request, pk, user_id):
    group = get_object_or_404(NamingGroup, pk=pk)
    if group.owner != request.user:
        raise PermissionDenied
    if user_id == request.user.id:
        messages.error(request, "You can't remove yourself as owner.")
        return redirect('group_detail', pk=pk)
    membership = get_object_or_404(GroupMembership, group=group, user_id=user_id)
    membership.delete()
    messages.success(request, 'Member removed.')
    return redirect('group_detail', pk=pk)


@login_required
def invite_view(request, token):
    group = get_object_or_404(NamingGroup, invite_token=token)
    already_member = group.members.filter(id=request.user.id).exists()

    if request.method == 'POST':
        if not already_member:
            GroupMembership.objects.create(user=request.user, group=group)
            messages.success(request, f'You joined "{group.name}"!')
        else:
            messages.info(request, f'You are already a member of "{group.name}".')
        return redirect('group_detail', pk=group.pk)

    return render(request, 'groups/invite.html', {
        'group': group,
        'already_member': already_member,
    })


def _swipe_queue(user, sex_filter):
    qs = NameGroup.objects.prefetch_related('variants')
    if sex_filter in ('M', 'F', 'N'):
        qs = qs.filter(sex=sex_filter)

    decided_ids = set(
        Swipe.objects.filter(user=user, decision__in=[Swipe.LIKE, Swipe.DISLIKE])
        .values_list('name_group_id', flat=True)
    )
    skipped_ids = set(
        Swipe.objects.filter(user=user, decision=Swipe.SKIP)
        .values_list('name_group_id', flat=True)
    )

    unswiped, skipped = [], []
    for ng in qs:
        if ng.id in decided_ids:
            continue
        if ng.id in skipped_ids:
            skipped.append(ng)
        else:
            unswiped.append(ng)

    return unswiped + skipped


@login_required
def swipe_view(request):
    sex_filter = request.GET.get('sex', '')
    queue = _swipe_queue(request.user, sex_filter)

    names_data = [
        {
            'id': ng.id,
            'display': ' / '.join(ng.variants.values_list('name', flat=True)),
            'sex': ng.get_sex_display(),
        }
        for ng in queue
    ]

    return render(request, 'names/swipe.html', {
        'names_data_json': json.dumps(names_data),
        'sex_filter': sex_filter,
        'remaining': len(queue),
    })


@login_required
@require_POST
def swipe_action(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name_group_id = data.get('name_group_id')
    decision = data.get('decision')

    if decision not in (Swipe.LIKE, Swipe.DISLIKE, Swipe.SKIP):
        return JsonResponse({'error': 'Invalid decision'}, status=400)

    ng = get_object_or_404(NameGroup, id=name_group_id)
    Swipe.objects.update_or_create(
        user=request.user,
        name_group=ng,
        defaults={'decision': decision},
    )
    return JsonResponse({'success': True})


@login_required
def swipe_history(request):
    sex_filter = request.GET.get('sex', '')
    swipes = (
        request.user.swipes
        .select_related('name_group')
        .prefetch_related('name_group__variants')
    )
    if sex_filter in ('M', 'F', 'N'):
        swipes = swipes.filter(name_group__sex=sex_filter)
    swipes = swipes.order_by('-updated_at')

    return render(request, 'names/swipe_history.html', {
        'swipes': swipes,
        'sex_filter': sex_filter,
        'decisions': Swipe.DECISION_CHOICES,
    })


@login_required
@require_POST
def swipe_edit(request, swipe_id):
    swipe = get_object_or_404(Swipe, id=swipe_id, user=request.user)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    decision = data.get('decision')
    if decision not in (Swipe.LIKE, Swipe.DISLIKE, Swipe.SKIP):
        return JsonResponse({'error': 'Invalid decision'}, status=400)

    swipe.decision = decision
    swipe.save()
    return JsonResponse({'success': True, 'new_decision': decision})


def _matched_names(naming_group, sex_filter):
    members = naming_group.members.all()
    qs = NameGroup.objects.prefetch_related('variants')
    if sex_filter in ('M', 'F', 'N'):
        qs = qs.filter(sex=sex_filter)
    for member in members:
        liked = Swipe.objects.filter(
            user=member, decision=Swipe.LIKE
        ).values_list('name_group_id', flat=True)
        qs = qs.filter(id__in=liked)
    return qs


@login_required
def score_view(request, group_id):
    naming_group = get_object_or_404(NamingGroup, id=group_id)
    if not naming_group.members.filter(id=request.user.id).exists():
        raise PermissionDenied

    sex_filter = request.GET.get('sex', '')
    matched = _matched_names(naming_group, sex_filter)

    user_scores = {
        s.name_group_id: s
        for s in Score.objects.filter(
            user=request.user, name_group__in=matched
        ).prefetch_related('preferred_variants')
    }

    names_with_scores = []
    for ng in matched:
        score = user_scores.get(ng.id)
        names_with_scores.append({
            'name_group': ng,
            'score': score,
            'preferred_variant_ids': list(score.preferred_variants.values_list('id', flat=True)) if score else [],
        })

    return render(request, 'names/score.html', {
        'naming_group': naming_group,
        'names_with_scores': names_with_scores,
        'sex_filter': sex_filter,
    })


@login_required
@require_POST
def score_save(request, group_id):
    naming_group = get_object_or_404(NamingGroup, id=group_id)
    if not naming_group.members.filter(id=request.user.id).exists():
        raise PermissionDenied

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name_group_id = data.get('name_group_id')
    stars = data.get('stars')
    preferred_variant_ids = data.get('preferred_variant_ids', [])
    comment = data.get('comment', '').strip()

    if not isinstance(stars, int) or not (1 <= stars <= 5):
        return JsonResponse({'error': 'Stars must be 1–5'}, status=400)

    ng = get_object_or_404(NameGroup, id=name_group_id)
    score, _ = Score.objects.update_or_create(
        user=request.user,
        name_group=ng,
        defaults={'stars': stars, 'comment': comment},
    )
    valid_variants = NameVariant.objects.filter(id__in=preferred_variant_ids, group=ng)
    score.preferred_variants.set(valid_variants)

    return JsonResponse({'success': True})


@login_required
def results_view(request, group_id):
    naming_group = get_object_or_404(NamingGroup, id=group_id)
    if not naming_group.members.filter(id=request.user.id).exists():
        raise PermissionDenied

    sex_filter = request.GET.get('sex', '')
    members = list(naming_group.members.all())
    matched = _matched_names(naming_group, sex_filter)
    matched = matched.prefetch_related('variants', 'scores__user', 'scores__preferred_variants')

    results = []
    member_ids = {m.id for m in members}
    for ng in matched:
        member_scores = [s for s in ng.scores.all() if s.user_id in member_ids]
        avg = sum(s.stars for s in member_scores) / len(member_scores) if member_scores else 0

        per_member = []
        for member in members:
            score = next((s for s in member_scores if s.user_id == member.id), None)
            per_member.append({'user': member, 'score': score})

        results.append({
            'name_group': ng,
            'avg_score': avg,
            'per_member': per_member,
        })

    results.sort(key=lambda x: x['avg_score'], reverse=True)

    return render(request, 'names/results.html', {
        'naming_group': naming_group,
        'results': results,
        'sex_filter': sex_filter,
        'members': members,
    })
