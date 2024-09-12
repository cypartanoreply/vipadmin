from django.db import models

from django.contrib.auth.models import User,Group

from CypartaGraphqlSubscriptionsTools.mixins import CypartaSubscriptionModelMixin
from django.utils.translation import gettext_lazy as _
class User(CypartaSubscriptionModelMixin, User):
    class Meta:
        proxy = True
class Group(CypartaSubscriptionModelMixin, Group):
    class Meta:
        proxy = True
class Employee(CypartaSubscriptionModelMixin,models.Model):
    upload_files_path='files/'
    name = models.CharField(max_length=100,help_text='name of employee')
    salay=models.FloatField()
    image = models.FileField(upload_to=upload_files_path, verbose_name=_('imag Field1'),null=True,blank=True)
    image1 = models.FileField(upload_to=upload_files_path, verbose_name=_('imag Field2'),null=True,blank=True)
    image2= models.FileField(upload_to=upload_files_path, verbose_name=_('imag Field3'),null=True,blank=True)
    image3 = models.FileField(upload_to=upload_files_path, verbose_name=_('imag Field4'),null=True,blank=True)
    many_users = models.ManyToManyField(User, related_name='many_to_many_users_set', verbose_name=_('Many-to-Many users Field'))
    

    def __str__(self):
        return self.name +'with salary ' +str(self.salay)
class OtherModel(CypartaSubscriptionModelMixin,models.Model):
    name = models.CharField(max_length=100)
    emp = models.ForeignKey(Employee, blank=True,null =True,on_delete=models.CASCADE, related_name='Employee_foreign_key_set', verbose_name=_('Employee_Foreign Key Field'))
    def __str__(self):
        return self.name



class AllTypeModel(CypartaSubscriptionModelMixin, models.Model):
    class Meta:
        verbose_name = _('AllTypeModel')
        verbose_name_plural = _('AllTypeModel')
    # Field names
    big_integer_field = models.BigIntegerField(verbose_name=_('Big Integer Field'))
    boolean_field = models.BooleanField(verbose_name=_('Boolean Field'), null=True)
    boolean_field2 = models.BooleanField(verbose_name=_('Boolean Field'), null=True,blank=True)
    
    char_field = models.CharField(max_length=100, verbose_name=_('Character Field'), default=_('ahmed'))
    date_field = models.DateField(verbose_name=_('Date Field'))
    datetime_field = models.DateTimeField(verbose_name=_('Datetime Field'))
    decimal_field = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Decimal Field'))
    duration_field = models.DurationField(verbose_name=_('Duration Field'))
    email_field = models.EmailField(verbose_name=_('Email Field'))
    file_field = models.FileField(upload_to='files/', verbose_name=_('File Field'))
    float_field = models.FloatField(verbose_name=_('Float Field'))
    image_field = models.ImageField(upload_to='images/', verbose_name=_('Image Field'))
    integer_field = models.IntegerField(verbose_name=_('Integer Field'))
    generic_ip_address_field = models.GenericIPAddressField(verbose_name=_('Generic IP Address Field'))
    positive_big_integer_field = models.PositiveBigIntegerField(verbose_name=_('Positive Big Integer Field'))
    positive_integer_field = models.PositiveIntegerField(verbose_name=_('Positive Integer Field'))
    positive_small_integer_field = models.PositiveSmallIntegerField(verbose_name=_('Positive Small Integer Field'))
    slug_field = models.SlugField(verbose_name=_('Slug Field'))
    small_auto_field = models.SmallAutoField(primary_key=True, verbose_name=_('Small Auto Field'))
    small_integer_field = models.SmallIntegerField(verbose_name=_('Small Integer Field'))
    text_field = models.TextField(blank=True, verbose_name=_('Text Field'))
    time_field = models.TimeField(blank=True, verbose_name=_('Time Field'))
    url_field = models.URLField(verbose_name=_('URL Field'))
    uuid_field = models.UUIDField(verbose_name=_('UUID Field'))
    json_field = models.JSONField(verbose_name=_('JSON Field'))
    auto_slug_field = models.SlugField(auto_created=True, verbose_name=_('Auto Slug Field'))
    foreign_key_field = models.ForeignKey(OtherModel, on_delete=models.CASCADE, related_name='foreign_key_set', verbose_name=_('Foreign Key Field'))
    one_to_one_field = models.OneToOneField(OtherModel, on_delete=models.CASCADE, related_name='one_to_one', verbose_name=_('One-to-One Field'))
    many_to_many_field = models.ManyToManyField(OtherModel, related_name='many_to_many_set', verbose_name=_('Many-to-Many Field'))
    many_Employee = models.ManyToManyField(Employee, related_name='many_to_many_Employee_set', verbose_name=_('Many-to-Many Employee Field'))
    
    # Choices
    PAYMENT_METHOD_CHOICES = (
        ('BANK', _('Bank')),
        ('CRYPTO', _('Crypto')),
    )
    
    class Genre(models.TextChoices):
        FICTION = 'F', _('Fiction')
        NON_FICTION = 'NF', _('Non-Fiction')
        SCIENCE_FICTION = 'SF', _('Science Fiction')
    choice_filed = models.CharField(max_length=100,choices=Genre.choices,null=True,blank=True)


