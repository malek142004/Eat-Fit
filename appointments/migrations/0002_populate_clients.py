from django.db import migrations

def create_sample_clients(apps, schema_editor):
    Client = apps.get_model('appointments', 'Client')
    clients_to_create = []
    for i in range(1, 6):
        clients_to_create.append(
            Client(first_name=f'ClientFname{i}', last_name=f'ClientLname{i}', email=f'client{i}@example.com')
        )
    Client.objects.bulk_create(clients_to_create)

def delete_sample_clients(apps, schema_editor):
    Client = apps.get_model('appointments', 'Client')
    for i in range(1, 6):
        Client.objects.filter(email=f'client{i}@example.com').delete()

class Migration(migrations.Migration):
    dependencies = [('appointments', '0001_initial')]
    operations = [migrations.RunPython(create_sample_clients, delete_sample_clients)]