# Generated by Django 2.1 on 2018-08-19 00:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0047_auto_20180818_2000'),
    ]

    operations = [
        migrations.CreateModel(
            name='GPersonFinderNote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note_record_id', models.CharField(max_length=200)),
                ('entry_date', models.CharField(max_length=20)),
                ('author_name', models.CharField(blank=True, max_length=500)),
                ('author_email', models.CharField(blank=True, max_length=200)),
                ('author_phone', models.CharField(blank=True, max_length=30)),
                ('linked_pf_record_id', models.CharField(blank=True, max_length=200)),
                ('original_creation_date', models.CharField(blank=True, max_length=20)),
                ('source_date', models.CharField(blank=True, max_length=20)),
                ('status', models.CharField(blank=True, choices=[('', 'Unspecified'), ('information_sought', 'Information Sought'), ('is_note_author', 'Is Note Author'), ('believed_alive', 'Believed Alive'), ('believed_missing', 'Believed Missing'), ('believed_dead', 'Believed Dead')], max_length=25)),
                ('author_made_contact', models.BooleanField(null=True)),
                ('email_of_found_person', models.CharField(blank=True, max_length=200)),
                ('phone_of_found_person', models.CharField(blank=True, max_length=30)),
                ('last_known_location', models.CharField(blank=True, max_length=500)),
                ('text', models.TextField(blank=True)),
                ('photo_url', models.CharField(blank=True, max_length=250)),
            ],
        ),
        migrations.CreateModel(
            name='GPersonFinderRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('person_record_id', models.CharField(max_length=200)),
                ('entry_date', models.CharField(max_length=20)),
                ('expiry_date', models.CharField(max_length=20)),
                ('author_name', models.CharField(blank=True, max_length=500)),
                ('author_email', models.CharField(blank=True, max_length=200)),
                ('author_phone', models.CharField(blank=True, max_length=30)),
                ('original_creation_date', models.CharField(max_length=20, null=True)),
                ('source_date', models.CharField(max_length=20, null=True)),
                ('source_name', models.CharField(blank=True, max_length=200)),
                ('source_url', models.CharField(blank=True, max_length=200)),
                ('full_name', models.CharField(blank=True, max_length=500)),
                ('given_name', models.CharField(blank=True, max_length=500)),
                ('family_name', models.CharField(blank=True, max_length=500)),
                ('alternate_names', models.CharField(blank=True, max_length=500)),
                ('description', models.TextField(blank=True)),
                ('sex', models.CharField(blank=True, max_length=6)),
                ('date_of_birth', models.CharField(blank=True, max_length=20)),
                ('age', models.CharField(blank=True, max_length=15)),
                ('home_street', models.CharField(blank=True, max_length=500)),
                ('home_neighborhood', models.CharField(blank=True, max_length=50)),
                ('home_city', models.CharField(blank=True, max_length=50)),
                ('home_state', models.CharField(blank=True, max_length=50)),
                ('home_postal_code', models.CharField(blank=True, max_length=130)),
                ('home_country', models.CharField(blank=True, max_length=20)),
                ('photo_url', models.CharField(blank=True, max_length=250)),
                ('profile_urls', models.CharField(blank=True, max_length=400)),
                ('is_duplicate_of_person', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='mainapp.Person')),
                ('is_duplicate_of_req', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='mainapp.Request')),
            ],
        ),
        migrations.AddField(
            model_name='gpersonfindernote',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mainapp.GPersonFinderRecord'),
        ),
    ]
