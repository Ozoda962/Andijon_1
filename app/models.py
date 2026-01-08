from django.db import models

class Direction(models.Model):
    title = models.CharField(max_length=255)
    logo = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title
    

class Location(models.Model):
    title = models.CharField(max_length=255,blank=True,null=True)
    direction = models.ForeignKey(        
        Direction,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="direction_locations"
    )

    def __str__(self):
        return self.title
    

class Section(models.Model):
    title = models.CharField(max_length=255)
    about = models.TextField(max_length=500,blank=True, null=True)
    photo = models.FileField(upload_to="sections/", blank=True, null=True)
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="location_sections"    
    )
    direction = models.ForeignKey(
    Direction,
    on_delete=models.CASCADE,
    related_name="direction_sections"
    )

    def __str__(self):
        return self.title
    

class Datchik(models.Model):
    title = models.CharField(max_length=255,blank=False)
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="location_datchiks"    
    )
    direction = models.ForeignKey(
        Direction,
        on_delete=models.CASCADE,
        related_name="direction_datchiks"
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="section_datchiks" 
    )
    criterion_1 = models.FloatField(null=True, blank=True)
    criterion_2 = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.title
    
class DatchikLog(models.Model):
    datchik = models.ForeignKey(
        Datchik,
        on_delete=models.CASCADE,
        related_name="logs"
    )
    record_date = models.DateTimeField(null=True,blank=True)
    pressure = models.FloatField(null=True, blank=True)
    water_high_pizometr = models.FloatField(null=True, blank=True)
    water_high_bef = models.FloatField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    water_consumption = models.FloatField(null=True, blank=True)
    blur_level = models.FloatField(null=True, blank=True)
    deviation_indicator = models.FloatField(null=True, blank=True)
    sin_A = models.FloatField(null=True, blank=True)
    sin_B = models.FloatField(null=True, blank=True)
    shift_X = models.FloatField(null=True, blank=True)
    shift_Y = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)



class DatchikFormula(models.Model):
    datchik = models.OneToOneField(
        Datchik,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="formula"
    )
    formula = models.CharField(max_length=255)

    A = models.FloatField(null=True, blank=True)
    B = models.FloatField(null=True, blank=True)
    C = models.FloatField(null=True, blank=True)
    D = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Formula for {self.datchik.title}-{self.formula}"