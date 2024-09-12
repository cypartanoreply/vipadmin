from django.core.management.base import BaseCommand
from faker import Faker
import random

# Import your Django models
from vipadmin.models import OtherModel, AllTypeModel
from datetime import timedelta
class Command(BaseCommand):
    help = 'Generate fake data for testing purposes'

    # Function to generate fake data for OtherModel
    def generate_fake_other_model_data(self, num_records):
        fake = Faker()
        for _ in range(num_records):
            name = fake.name()
            OtherModel.objects.create(name=name)

    # Function to generate fake data for AllTypeModel
    def generate_fake_all_type_model_data(self, num_records):
        fake = Faker()
        for _ in range(num_records):
            # Generate fake start and end times
            start_time = fake.date_time_this_year(before_now=True, after_now=False)
            end_time = fake.date_time_this_year(before_now=False, after_now=True)
            # Calculate the duration between start and end times
            duration = end_time - start_time
            # Convert duration to total seconds (or any other unit you prefer)
            total_seconds = duration.total_seconds()
            instance = AllTypeModel.objects.create(
                big_integer_field=random.randint(-9223372036854775808, 9223372036854775807),
                boolean_field=fake.boolean(),
                char_field=fake.word(),
                date_field=fake.date(),
                datetime_field=fake.date_time(),
               decimal_field=fake.pydecimal(left_digits=5, right_digits=2, positive=True),
               duration_field=timedelta(seconds=total_seconds),
                email_field=fake.email(),
                float_field=random.uniform(-3.4e38, 3.4e38),
                image_field=None,  # Replace with actual image if needed
                integer_field=random.randint(-2147483648, 2147483647),
                generic_ip_address_field=fake.ipv4(),
                positive_big_integer_field=random.randint(0, 9223372036854775807),
                positive_integer_field=random.randint(0, 2147483647),
                positive_small_integer_field=random.randint(0, 32767),
                slug_field=fake.slug(),
                small_integer_field=random.randint(-32768, 32767),
                text_field=fake.text(),
                time_field=fake.time(),
                url_field=fake.url(),
                uuid_field=fake.uuid4(),
                json_field={},  # Replace with actual JSON data if needed
                #auto_slug_field=None,  # Replace with auto-generated slug if needed
                #file_path_field=fake.file_path(depth=1),  # Adjust depth as needed
                foreign_key_field=random.choice(OtherModel.objects.all()),
               one_to_one_field_id=random.randint(51, 100),
               one_to_one_field=random.choice(OtherModel.objects.all())
            )
            # Add ManyToManyField and OneToOneField data if applicable
            instance.many_to_many_field.set(OtherModel.objects.all())
            #instance.one_to_one_field = random.choice(OtherModel.objects.all())
            instance.save()

    def handle(self, *args, **options):
        # Define the number of records to generate
        num_records = 10

        # Generate fake data for OtherModel
        self.generate_fake_other_model_data(num_records)

        # Generate fake data for AllTypeModel
        self.generate_fake_all_type_model_data(num_records)
