# Generated by Django 2.2.16 on 2022-11-19 19:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("posts", "0008_auto_20221119_1245"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="pub_date",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="Дата публикации"
            ),
        ),
        migrations.AlterField(
            model_name="post",
            name="pub_date",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="Дата публикации"
            ),
        ),
    ]
