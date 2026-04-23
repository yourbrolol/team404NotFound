from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ("app", "0021_alter_team_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="JuryAssignment",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                ("contest", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="jury_assignments", to="app.contest")),
                ("team", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="jury_assignments", to="app.team")),
                ("jury_member", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="jury_assignments", to="app.user")),
            ],
            options={
                "unique_together": {("contest", "team", "jury_member")},
                "verbose_name": "Jury Assignment",
                "verbose_name_plural": "Jury Assignments",
            },
        ),
    ]