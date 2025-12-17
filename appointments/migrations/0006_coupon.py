"""Create Coupon model"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0005_wallet'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=32, unique=True)),
                ('amount', models.DecimalField(max_digits=7, decimal_places=2)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('redeemed', models.BooleanField(default=False)),
                ('redeemed_at', models.DateTimeField(null=True, blank=True)),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='coupons', to='users.customuser')),
            ],
        ),
    ]
