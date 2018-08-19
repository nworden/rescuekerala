import collections
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.base import TemplateView
from .models import Request, Volunteer, DistrictManager, Contributor, DistrictNeed, Person, RescueCamp, NGO, Announcements, GPersonFinderRecord, GPersonFinderNote
import django_filters
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.db.models import Count, QuerySet
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import Http404
from mainapp.admin import create_csv_response
from floodrelief import settings as floodrelief_settings
from mainapp.utils import pfif
import urllib

class CreateRequest(CreateView):
    model = Request
    template_name='mainapp/request_form.html'
    fields = [
        'district',
        'location',
        'requestee',
        'requestee_phone',
        'is_request_for_others',
        'latlng',
        'latlng_accuracy',
        'needrescue',
        'detailrescue',
        'needwater',
        'detailwater',
        'needfood',
        'detailfood',
        'needcloth',
        'detailcloth',
        'needmed',
        'detailmed',
        'needkit_util',
        'detailkit_util',
        'needtoilet',
        'detailtoilet',
        'needothers'
    ]
    success_url = '/req_sucess/'


class RegisterVolunteer(CreateView):
    model = Volunteer
    fields = ['name', 'district', 'phone', 'organisation', 'area', 'address']
    success_url = '/reg_success/'


class RegisterNGO(CreateView):
    model = NGO
    fields = ['organisation', 'organisation_type','organisation_address', 'name', 'phone', 'description', 'area',
              'location']
    success_url = '/reg_success'


def download_ngo_list(request):
    district = request.GET.get('district', None)
    filename = 'ngo_list.csv'
    if district is not None:
        filename = 'ngo_list_{0}.csv'.format(district)
        qs = NGO.objects.filter(district=district).order_by('district','name')
    else:
        qs = NGO.objects.all().order_by('district','name')
    header_row = ['Organisation',
                  'Type',
                  'Address',
                  'Name',
                  'Phone',
                  'Description',
                  'District',
                  'Area',
                  'Location',
                  ]
    body_rows = qs.values_list(
        'organisation',
        'organisation_type',
        'organisation_address',
        'name',
        'phone',
        'description',
        'district',
        'area',
        'location',
    )
    return create_csv_response(filename, header_row, body_rows)

class RegisterContributor(CreateView):
    model = Contributor
    fields = ['name', 'district', 'phone', 'address',  'commodities']
    success_url = '/contrib_success/'


class HomePageView(TemplateView):
    template_name = "home.html"


class NgoVolunteerView(TemplateView):
    template_name = "ngo_volunteer.html"


class MapView(TemplateView):
    template_name = "mapview.html"


class ReqSuccess(TemplateView):
    template_name = "mainapp/req_success.html"

class RegSuccess(TemplateView):
    template_name = "mainapp/reg_success.html"


class ContribSuccess(TemplateView):
    template_name = "mainapp/contrib_success.html"

class DisclaimerPage(TemplateView):
    template_name = "mainapp/disclaimer.html"

class AboutIEEE(TemplateView):
    template_name = "mainapp/aboutieee.html"

class DistNeeds(TemplateView):
    template_name = "mainapp/district_needs.html"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['district_data'] = DistrictNeed.objects.all()
        return context

class RescueCampFilter(django_filters.FilterSet):
    class Meta:
        model = RescueCamp
        fields = ['district']

    def __init__(self, *args, **kwargs):
        super(RescueCampFilter, self).__init__(*args, **kwargs)
        # at startup user doen't push Submit button, and QueryDict (in data) is empty
        if self.data == {}:
            self.queryset = self.queryset.none()

def relief_camps(request):
    filter = RescueCampFilter(request.GET, queryset=RescueCamp.objects.all())
    relief_camps = filter.qs.annotate(count=Count('person')).order_by('district','name').all()

    return render(request, 'mainapp/relief_camps.html', {'filter': filter , 'relief_camps' : relief_camps, 'district_chosen' : len(request.GET.get('district') or '')>0 })

class RequestFilter(django_filters.FilterSet):
    class Meta:
        model = Request
        # fields = ['district', 'status', 'needwater', 'needfood', 'needcloth', 'needmed', 'needkit_util', 'needtoilet', 'needothers',]

        fields = {
                    'district' : ['exact'],
                    'requestee' : ['icontains'],
                    'requestee_phone' : ['exact'],
                    'location' : ['icontains']
                 }

    def __init__(self, *args, **kwargs):
        super(RequestFilter, self).__init__(*args, **kwargs)
        # at startup user doen't push Submit button, and QueryDict (in data) is empty
        if self.data == {}:
            self.queryset = self.queryset.none()


def request_list(request):
    filter = RequestFilter(request.GET, queryset=Request.objects.all() )
    req_data = filter.qs.order_by('-id')
    paginator = Paginator(req_data, 100)
    page = request.GET.get('page')
    req_data = paginator.get_page(page)
    return render(request, 'mainapp/request_list.html', {'filter': filter , "data" : req_data })

def request_details(request, request_id=None):
    if not request_id:
        return HttpResponseRedirect("/error?error_text={}".format('Page not found!'))
    filter = RequestFilter(None)
    try:
        req_data = Request.objects.get(id=request_id)
    except:
        return HttpResponseRedirect("/error?error_text={}".format('Sorry, we couldnt fetch details for that request'))
    return render(request, 'mainapp/request_details.html', {'filter' : filter, 'req': req_data })

class DistrictManagerFilter(django_filters.FilterSet):
    class Meta:
        model = DistrictManager
        fields = ['district']

    def __init__(self, *args, **kwargs):
        super(DistrictManagerFilter, self).__init__(*args, **kwargs)
        # at startup user doen't push Submit button, and QueryDict (in data) is empty
        if self.data == {}:
            self.queryset = self.queryset.none()

def districtmanager_list(request):
    filter = DistrictManagerFilter(request.GET, queryset=DistrictManager.objects.all())
    return render(request, 'mainapp/districtmanager_list.html', {'filter': filter})

class Maintenance(TemplateView):
    template_name = "mainapp/maintenance.html"


def mapdata(request):
    district = request.GET.get("district", "all")
    data = cache.get("mapdata:" + district)
    if data:
        return JsonResponse(list(data) , safe=False)
    if district != "all":
        data = Request.objects.exclude(latlng__exact="").filter(district=district).values()
    else:
        data = Request.objects.exclude(latlng__exact="").values()
    cache.set("mapdata:" + district, data, settings.CACHE_TIMEOUT)
    return JsonResponse(list(data) , safe=False)

def mapview(request):
    return render(request,"map.html")

def dmodash(request):
    return render(request , "dmodash.html")

def dmoinfo(request):
    if("district" not in request.GET.keys()):return HttpResponseRedirect("/")
    dist = request.GET.get("district")
    reqserve = Request.objects.all().filter(status = "sup" , district = dist).count()
    reqtotal = Request.objects.all().filter(district = dist).count()
    volcount = Volunteer.objects.all().filter(district = dist).count()
    conserve = Contributor.objects.all().filter(status = "ful" , district = dist).count()
    contotal = Contributor.objects.all().filter(district = dist).count()
    return render(request ,"dmoinfo.html",{"reqserve" : reqserve , "reqtotal" : reqtotal , "volcount" : volcount , "conserve" : conserve , "contotal" : contotal })

def error(request):
    error_text = request.GET.get('error_text')
    return render(request , "mainapp/error.html", {"error_text" : error_text})

def logout_view(request):
    logout(request)
    # Redirect to camps page instead
    return redirect('/relief_camps')

class PersonForm(forms.ModelForm):
    class Meta:
       model = Person
       fields = [
        'camped_at',
        'name',
        'phone',
        'age',
        'gender',
        'district',
        'address',
        'notes'
        ]
       
       widgets = {
           'address': forms.Textarea(attrs={'rows':3}),
           'notes': forms.Textarea(attrs={'rows':3}),
           'gender': forms.RadioSelect(),
        }


    def __init__(self, *args, **kwargs):
       camp_id = kwargs.pop('camp_id')
       super(PersonForm, self).__init__(*args, **kwargs)
       rescue_camp_qs = RescueCamp.objects.filter(id=camp_id)
       self.fields['camped_at'].queryset = rescue_camp_qs
       self.fields['camped_at'].initial = rescue_camp_qs.first()

class AddPerson(SuccessMessageMixin,LoginRequiredMixin,CreateView):
    login_url = '/login/'
    model = Person
    template_name='mainapp/add_person.html'  
    form_class = PersonForm
    success_message = "'%(name)s' registered successfully"

    def get_success_url(self):
        return reverse('add_person', args=(self.camp_id,))

    def dispatch(self, request, *args, **kwargs):
        self.camp_id = kwargs.get('camp_id','')
        
        try:
            self.camp = RescueCamp.objects.get(id=int(self.camp_id))
        except ObjectDoesNotExist:
            raise Http404

        # Commented to allow all users to edit all camps
        # if request.user!=self.camp.data_entry_user:
        #     raise PermissionDenied

        return super(AddPerson, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(AddPerson, self).get_form_kwargs()
        kwargs['camp_id'] = self.camp_id
        return kwargs


class CampRequirementsForm(forms.ModelForm):
    class Meta:
       model = RescueCamp
       fields = [
        'name',
        'total_people',
        'total_males',
        'total_females',
        'total_infants',
        'food_req',
        'clothing_req',
        'sanitary_req',
        'medical_req',
        'other_req'
        ]
       read_only = ('name',)
       widgets = {
           'name': forms.Textarea(attrs={'rows':1,'readonly':True}),
           'food_req': forms.Textarea(attrs={'rows':3}),
           'clothing_req': forms.Textarea(attrs={'rows':3}),
           'medical_req': forms.Textarea(attrs={'rows':3}),
           'sanitary_req': forms.Textarea(attrs={'rows':3}),
           'other_req': forms.Textarea(attrs={'rows':3}),
       }

class CampRequirements(SuccessMessageMixin,LoginRequiredMixin,UpdateView):
    login_url = '/login/'
    model = RescueCamp
    template_name='mainapp/camp_requirements.html'  
    form_class = CampRequirementsForm
    success_url = '/coordinator_home/'
    success_message = "Updated requirements saved!"

    # Commented to allow all users to edit all camps
    # def dispatch(self, request, *args, **kwargs):
    #     if request.user!=self.get_object().data_entry_user:
    #         raise PermissionDenied
    #     return super(CampDetails, self).dispatch(
    #         request, *args, **kwargs)


class CampDetailsForm(forms.ModelForm):
    class Meta:
       model = RescueCamp
       fields = [
        'name',
        'location',
        'district',
        'taluk',
        'village',
        'contacts',
        'map_link',
        'latlng',
        ]

class CampDetails(SuccessMessageMixin,LoginRequiredMixin,UpdateView):
    login_url = '/login/'
    model = RescueCamp
    template_name='mainapp/camp_details.html'  
    form_class = CampDetailsForm
    success_url = '/coordinator_home/'
    success_message = "Details saved!"

    # Commented to allow all users to edit all camps
    # def dispatch(self, request, *args, **kwargs):
    #     if request.user!=self.get_object().data_entry_user:
    #         raise PermissionDenied
    #     return super(CampDetails, self).dispatch(
    #         request, *args, **kwargs)


class PeopleFilter(django_filters.FilterSet):
    fields = ['name', 'phone','address','district','notes','gender','camped_at']

    class Meta:
        model = Person
        fields = {
            'name' : ['icontains'],
            'phone' : ['icontains'],
            'address' : ['icontains'],
            'district' : ['exact'],
            'notes':['icontains'],
            'gender':['exact'],
            'camped_at':['exact']
        }

        # TODO - field order seems to not be working!
        # field_order = ['name', 'phone', 'address','district','notes','gender','camped_at']

    def __init__(self, *args, **kwargs):
        super(PeopleFilter, self).__init__(*args, **kwargs)
        if self.data == {}:
            self.queryset = self.queryset.all()

def find_people(request):
    filter = PeopleFilter(request.GET, queryset=Person.objects.all())
    people = filter.qs.order_by('name','-added_at')
    paginator = Paginator(people, 50)
    page = request.GET.get('page')
    people = paginator.get_page(page)
    return render(request, 'mainapp/people.html', {'filter': filter , "data" : people })

class AnnouncementFilter(django_filters.FilterSet):
    class Meta:
        model = Announcements
        fields = ['district', 'category']

    def __init__(self, *args, **kwargs):
        super(AnnouncementFilter, self).__init__(*args, **kwargs)
        if self.data == {}:
            self.queryset = self.queryset.none()

def announcements(request):
    filter = AnnouncementFilter(request.GET, queryset=Announcements.objects.all())
    link_data = filter.qs.order_by('-id')
    # As per the discussions orddering by id hoping they would be addded in order
    paginator = Paginator(link_data, 10)
    page = request.GET.get('page')
    link_data = paginator.get_page(page)
    return render(request, 'announcements.html', {'filter': filter, "data" : link_data})

class CoordinatorCampFilter(django_filters.FilterSet):
    class Meta:
        model = RescueCamp
        fields = {
            'district' : ['exact'],
            'name' : ['icontains']
        }
    
    def __init__(self, *args, **kwargs):
        super(CoordinatorCampFilter, self).__init__(*args, **kwargs)
        if self.data == {}:
            self.queryset = self.queryset.none()

@login_required(login_url='/login/')
def coordinator_home(request):
    filter = CoordinatorCampFilter(request.GET, queryset=RescueCamp.objects.all())
    data = filter.qs.annotate(count=Count('person')).order_by('district','name').all()
    paginator = Paginator(data, 50)
    page = request.GET.get('page')
    data = paginator.get_page(page)

    return render(request, "mainapp/coordinator_home.html", {'filter': filter , 'data' : data})

class CampRequirementsFilter(django_filters.FilterSet):
    class Meta:
        model = RescueCamp
        fields = {
            'district' : ['exact'],
            'name' : ['icontains']
        }

    def __init__(self, *args, **kwargs):
        super(CampRequirementsFilter, self).__init__(*args, **kwargs)
        if self.data == {}:
            self.queryset = self.queryset.none()

def camp_requirements_list(request):
    filter = CampRequirementsFilter(request.GET, queryset=RescueCamp.objects.all())
    camp_data = filter.qs.order_by('name')
    paginator = Paginator(camp_data, 50)
    page = request.GET.get('page')
    data = paginator.get_page(page)
    return render(request, "mainapp/camp_requirements_list.html", {'filter': filter , 'data' : data})

def _gpersonfinder_import_process_person(p, counts):
    if 'person_record_id' not in p:
        counts['skipped: no person record ID'] += 1
        return
    existing_q = GPersonFinderRecord.objects.filter(
        person_record_id=p['person_record_id'])
    if existing_q.exists():
        record = existing_q[0]
        if record.entry_date >= p['entry_date']:
            counts['skipped: already stored entry'] += 1
            return
        is_update = True
    else:
        record = GPersonFinderRecord(person_record_id=p['person_record_id'])
        is_update = False
    record.FillFromPfifRecord(p)
    try:
        record.save()
        counts['updated record' if is_update else 'new record'] += 1
    except Exception as e:
        counts['skipped: error on saving record'] += 1
    return counts

def _gpersonfinder_import_persons(max_results):
    latest_record_q = GPersonFinderRecord.objects.order_by("-entry_date")
    if latest_record_q.exists():
        min_entry_date = (latest_record_q[0].entry_date)
    else:
        min_entry_date = "2018-01-01T01:02:03Z"
    print('min_entry_date: ' + min_entry_date)
    counts = collections.defaultdict(lambda: 0)
    offset = 0
    while offset < max_results:
        # PF returns a max of 200 at once.
        iter_max_results = min(200, max_results - offset)
        url = 'https://google.org/personfinder/2018-kerala-flooding/feeds/person?'
        arg_map = {
            'key': floodrelief_settings.env('GOOGLE_PERSON_FINDER_KEY'),
            'min_entry_date': min_entry_date,
            'skip': offset,
            'max_results': iter_max_results,
        }
        url += '&'.join(['%s=%s' % (k, v) for k, v in arg_map.items()])
        res = urllib.request.urlopen(url)
        pfif_records = pfif.parse_file(res, rename_fields=False)[0]
        if not pfif_records:
            counts['ended early, no more readable records'] += 1
            return counts
        for pfif_record in pfif_records:
            _gpersonfinder_import_process_person(pfif_record, counts)
        offset += iter_max_results
    return counts

def _gpersonfinder_import_process_note(n, counts):
    if 'person_record_id' not in n:
        counts['skipped: no person record ID'] += 1
        return
    person_record_q = GPersonFinderRecord.objects.filter(
        person_record_id=n['person_record_id'])
    if not person_record_q.exists():
        raise LookupError()
    if 'note_record_id' not in n:
        count['skipped: no note record ID'] += 1
        return
    existing_q = GPersonFinderNote.objects.filter(
        note_record_id=n['note_record_id'])
    if existing_q.exists():
        record = existing_q[0]
        if record.entry_date >= n['entry_date']:
            counts['skipped: already stored entry'] += 1
            return
        is_update = True
    else:
        record = GPersonFinderNote(note_record_id=n['note_record_id'])
        is_update = False
    record.FillFromPfifRecord(n)
    record.person = person_record_q[0]
    try:
        record.save()
        counts['updated record' if is_update else 'new record'] += 1
    except Exception as e:
        counts['skipped: error on saving record'] += 1
    return counts

def _gpersonfinder_import_notes(max_results):
    latest_record_q = GPersonFinderNote.objects.order_by("-entry_date")
    if latest_record_q.exists():
        min_entry_date = (latest_record_q[0].entry_date)
    else:
        min_entry_date = "2018-01-01T01:02:03Z"
    print('min_entry_date: ' + min_entry_date)
    counts = collections.defaultdict(lambda: 0)
    offset = 0
    while offset < max_results:
        # PF returns a max of 200 at once.
        iter_max_results = min(200, max_results - offset)
        url = 'https://google.org/personfinder/2018-kerala-flooding/feeds/note?'
        arg_map = {
            'key': floodrelief_settings.env('GOOGLE_PERSON_FINDER_KEY'),
            'min_entry_date': min_entry_date,
            'skip': offset,
            'max_results': iter_max_results,
        }
        url +='&'.join(['%s=%s' % (k, v) for k, v in arg_map.items()])
        res = urllib.request.urlopen(url)
        pfif_records = pfif.parse_file(res, rename_fields=False)[1]
        if not pfif_records:
            counts['ended early, no more readable records'] += 1
            return counts
        try:
            for pfif_record in pfif_records:
                _gpersonfinder_import_process_note(pfif_record, counts)
        except LookupError:
            counts['ended early, missing person record'] += 1
            return counts
        offset += iter_max_results
    return counts

def gpersonfinder_import(request):
    do_notes = request.GET['type'] == 'notes'
    max_results = int(request.GET['max_results']) or 1000
    if do_notes:
        counts = _gpersonfinder_import_notes(max_results)
    else:
        counts = _gpersonfinder_import_persons(max_results)
    res_output = ''
    for k, v in counts.items():
        res_output += '<br/>%s: %s' % (k, v)
    return HttpResponse(res_output.strip())
