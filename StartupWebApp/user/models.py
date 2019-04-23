from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User

# Create your models here.

class Defaultshippingaddress(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    address_line1 = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=200, blank=True, null=True)
    state = models.CharField(max_length=40, blank=True, null=True)
    zip = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=200, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)
    def __str__(self):
        return str(self.name) + ', ' + str(self.address_line1) + ', ' + str(self.city) + ', ' + str(self.state) + ' ' + str(self.zip) + ', ' + str(self.country_code)

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    newsletter_subscriber = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    email_verification_string = models.CharField(max_length=50, blank=True, null=True)
    email_verification_string_signed = models.CharField(max_length=200, blank=True, null=True)
    email_unsubscribed = models.BooleanField(default=False)
    email_unsubscribe_string = models.CharField(unique=True, max_length=50, null=True)
    email_unsubscribe_string_signed = models.CharField(unique=True, max_length=200, null=True)
    reset_password_string = models.CharField(max_length=50, blank=True, null=True)
    reset_password_string_signed = models.CharField(max_length=200, blank=True, null=True)
    mb_cd = models.CharField(unique=True, max_length=50, blank=True, null=True)
    stripe_customer_token = models.CharField(unique=True, max_length=100, blank=True, null=True)
    default_shipping_address = models.ForeignKey(Defaultshippingaddress, on_delete=models.CASCADE, blank=True, null=True)
    use_default_shipping_and_payment_info = models.BooleanField(default=False)
    def __str__(self):
        return self.user.username + ", Email: " + str(self.user.email)

class Prospect(models.Model):
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.CharField(unique=True, max_length=254, blank=True, null=True)
    phone = models.CharField(max_length=100, blank=True, null=True)
    email_unsubscribed = models.BooleanField(default=False)
    email_unsubscribe_string = models.CharField(unique=True, max_length=50, blank=True, null=True)
    email_unsubscribe_string_signed = models.CharField(unique=True, max_length=200, blank=True, null=True)
    prospect_comment = models.CharField(max_length=5000, blank=True, null=True)
    rg_comment = models.CharField(max_length=5000, blank=True, null=True)
    pr_cd = models.CharField(unique=True, max_length=50, blank=True, null=True)
    created_date_time = models.DateTimeField()
    converted_date_time = models.DateTimeField(blank=True, null=True)
    def __str__(self):
        return str(self.first_name) + " " + str(self.last_name) + ", Email: " + str(self.email)# + ", Prospect Code: " + str(self.pr_cd) + ", Email Unsubscribed String Signed: " + str(self.email_unsubscribe_string_signed)

class Emailunsubscribereasons(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, blank=True, null=True)
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE, blank=True, null=True)
    no_longer_want_to_receive = models.BooleanField(default=False)
    never_signed_up = models.BooleanField(default=False)
    inappropriate = models.BooleanField(default=False)
    spam = models.BooleanField(default=False)
    other = models.CharField(max_length=5000, blank=True, null=True)
    created_date_time = models.DateTimeField()
    def __str__(self):
        return "user: " + str(self.member.user.username if self.member is not None else None) + ", prospect: " + str(self.prospect.email if self.prospect is not None else None) + ", : " + str(self.no_longer_want_to_receive) + ", " + str(self.never_signed_up) + ", " + str(self.inappropriate) + ", " + str(self.spam) + ", " + str(self.other) + " @ " + str(self.created_date_time)

class EmailunsubscribereasonsAdmin(admin.ModelAdmin):
    list_display = ('member', 'prospect', 'no_longer_want_to_receive', 'never_signed_up', 'inappropriate', 'spam', 'other', 'created_date_time')

class Termsofuse(models.Model):
    version = models.IntegerField()
    version_note = models.CharField(max_length=1000, blank=True, null=True)
    publication_date_time = models.DateTimeField()
    class Meta:
        db_table = 'user_terms_of_use_version'
    def __str__(self):
        return str(self.version) + ":" + str(self.version_note) 

class Membertermsofuseversionagreed(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    termsofuseversion = models.ForeignKey(Termsofuse, on_delete=models.CASCADE)
    agreed_date_time = models.DateTimeField()
    class Meta:
        db_table = 'user_member_terms_of_use_version_agreed'
        unique_together = (('member', 'termsofuseversion'),)
    def __str__(self):
        return str(self.member.user.username) + ":" + str(self.termsofuseversion.version)

class Emailtype(models.Model):
    title = models.CharField(max_length=100)
    class Meta:
        db_table = 'user_email_type'
    def __str__(self):
        return self.title

class Emailstatus(models.Model):
    title = models.CharField(max_length=100)
    class Meta:
        db_table = 'user_email_status'
    def __str__(self):
        return self.title

class Email(models.Model):
    subject = models.CharField(max_length=300)
    email_type = models.ForeignKey(Emailtype, on_delete=models.CASCADE)
    email_status = models.ForeignKey(Emailstatus, on_delete=models.CASCADE)
    body_html = models.CharField(max_length=15000)
    body_text = models.CharField(max_length=5000)
    from_address = models.CharField(max_length=100)
    bcc_address = models.CharField(max_length=100)
    em_cd = models.CharField(unique=True, max_length=50, blank=True, null=True)
    class Meta:
        db_table = 'user_email'
    def __str__(self):
        return str(self.subject) + ": " + str(self.email_type) + ": " + str(self.email_status) 

class Emailsent(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, blank=True, null=True)
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE, blank=True, null=True)
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    sent_date_time = models.DateTimeField()
    class Meta:
        db_table = 'user_email_sent'
    def __str__(self):
        return "user: " + str(self.member.user.username if self.member is not None else None) + ", prospect: " + str(self.prospect.email if self.prospect is not None else None) + ", email: " + str(self.email.subject)

class Adtype(models.Model):
    title = models.CharField(max_length=100)
    class Meta:
        db_table = 'user_ad_type'
    def __str__(self):
        return self.title

class Adstatus(models.Model):
    title = models.CharField(max_length=100)
    class Meta:
        db_table = 'user_ad_status'
    def __str__(self):
        return self.title

class Ad(models.Model):
    campaignid = models.CharField(max_length=100, blank=True, null=True)
    adgroupid = models.CharField(max_length=100, blank=True, null=True)
    adid = models.CharField(max_length=100, blank=True, null=True)
    final_url = models.CharField(max_length=100, blank=True, null=True)
    headline_1 = models.CharField(max_length=30, blank=True, null=True)
    headline_2 = models.CharField(max_length=30, blank=True, null=True)
    headline_3 = models.CharField(max_length=30, blank=True, null=True)
    description_1 = models.CharField(max_length=90, blank=True, null=True)
    description_2 = models.CharField(max_length=90, blank=True, null=True)
    final_url_suffix = models.CharField(max_length=100, blank=True, null=True)
    ad_type = models.ForeignKey(Adtype, on_delete=models.CASCADE)
    ad_status = models.ForeignKey(Adstatus, on_delete=models.CASCADE)
    ad_cd = models.CharField(unique=True, max_length=50, blank=True, null=True)
    class Meta:
        db_table = 'user_ad'
    def __str__(self):
        return str(self.headline_1) + ": " + str(self.ad_type) + ": " + str(self.ad_status) 

class Chatmessage(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, blank=True, null=True)
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=150, blank=True, null=True)
    email_address = models.CharField(max_length=254, blank=True, null=True)
    message = models.CharField(max_length=5000, blank=True, null=True)
    created_date_time = models.DateTimeField()
    class Meta:
        db_table = 'user_chat_message'
    def __str__(self):
        return "user: " + str(self.member.user.username if self.member is not None else None) + ", prospect: " + str(self.prospect.email if self.prospect is not None else None) + ", name: " + str(self.name) + ", email_address: " + str(self.email_address) + ", message: " + str(self.message)




