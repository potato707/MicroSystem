# Generated migration to add new complaint admin permission fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr_management', '0045_alter_employeeattendance_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='teamcomplaintadminpermission',
            name='can_change_status',
            field=models.BooleanField(default=True, verbose_name='يمكن تغيير حالة الشكاوى'),
        ),
        migrations.AddField(
            model_name='teamcomplaintadminpermission',
            name='can_delete',
            field=models.BooleanField(default=False, verbose_name='يمكن حذف الشكاوى'),
        ),
        migrations.AddField(
            model_name='teamcomplaintadminpermission',
            name='can_manage_categories',
            field=models.BooleanField(default=False, verbose_name='يمكن إدارة الحالات المخصصة'),
        ),
        migrations.AddField(
            model_name='employeecomplaintadminpermission',
            name='can_change_status',
            field=models.BooleanField(default=True, verbose_name='يمكن تغيير حالة الشكاوى'),
        ),
        migrations.AddField(
            model_name='employeecomplaintadminpermission',
            name='can_delete',
            field=models.BooleanField(default=False, verbose_name='يمكن حذف الشكاوى'),
        ),
        migrations.AddField(
            model_name='employeecomplaintadminpermission',
            name='can_manage_categories',
            field=models.BooleanField(default=False, verbose_name='يمكن إدارة الحالات المخصصة'),
        ),
    ]
