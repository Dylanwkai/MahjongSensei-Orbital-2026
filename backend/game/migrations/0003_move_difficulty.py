from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0002_alter_move_id_alter_session_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='move',
            name='difficulty',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
