from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gyms', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gymimage',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='gyms/'),
        ),
        migrations.AddField(
            model_name='gymimage',
            name='external_url',
            field=models.URLField(blank=True, help_text='Optional externally hosted image URL for imported/demo listings.'),
        ),
        migrations.AddField(
            model_name='gymimage',
            name='source',
            field=models.CharField(blank=True, help_text='Image source, e.g. owner_upload, placeholder, google_places.', max_length=50),
        ),
        migrations.AddField(
            model_name='gymimage',
            name='credit',
            field=models.CharField(blank=True, help_text='Optional attribution/credit for external photos.', max_length=160),
        ),
    ]
