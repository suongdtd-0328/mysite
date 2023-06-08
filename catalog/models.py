# Used to generate URLs by reversing the URL patterns
from django.forms import ModelForm
import uuid  # Required for unique book instances
import datetime
from datetime import date
from django.urls import reverse
from django.db import models
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
# Create your models here.


class Genre(models.Model):
    """Model representing a book genre."""
    name = models.CharField(_('Name'), max_length=200,
                            help_text='Enter a book genre (e.g. Science Fiction)')

    def __str__(self):
        """String for representing the Model object."""
        return self.name


class Language(models.Model):
    """Model representing a Language (e.g. English, French, Japanese, etc.)"""
    name = models.CharField(max_length=200,
                            help_text="Enter the book's natural language (e.g. English, French, Japanese etc.)")

    def __str__(self):
        """String for representing the Model object (in Admin site etc.)"""
        return self.name


class Book(models.Model):
    """Model representing a book (but not a specific copy of a book)."""
    title = models.CharField(_('title'), max_length=200)

    # Foreign Key used because book can only have one author, but authors can have multiple books
    # Author is a string rather than an object because it hasn't been declared yet in the file
    author = models.ForeignKey('Author', on_delete=models.SET_NULL, null=True)

    summary = models.TextField(
        _('summary'), max_length=1000, help_text='Enter a brief description of the book')
    isbn = models.CharField(_('ISBN'), max_length=13, unique=True,
                            help_text='13 Character <a href="https://www.isbn-international.org/content/what-isbn">ISBN number</a>')

    # ManyToManyField used because genre can contain many books. Books can cover many genres.
    # Genre class has already been defined so we can specify the object above.
    genre = models.ManyToManyField(
        Genre, help_text='Select a genre for this book')

    def __str__(self):
        """String for representing the Model object."""
        return self.title

    def get_absolute_url(self):
        """Returns the URL to access a detail record for this book."""
        return reverse('book-detail', args=[str(self.id)])

    def display_genre(self):
        """Create a string for the Genre. This is required to display genre in Admin."""
        return ', '.join(genre.name for genre in self.genre.all()[:3])

    display_genre.short_description = _('Genre')


class BookInstance(models.Model):
    """Model representing a specific copy of a book (i.e. that can be borrowed from the library)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                          help_text='Unique ID for this particular book across whole library')
    book = models.ForeignKey('Book', on_delete=models.RESTRICT, null=True)
    imprint = models.CharField(_('imprint'), max_length=200)
    due_back = models.DateField(null=True, blank=True)

    LOAN_STATUS = (
        ('m', _('Maintenance')),
        ('o', _('On loan')),
        ('a', _('Available')),
        ('r', _('Reserved')),
    )

    status = models.CharField(_('status'),
                              max_length=1,
                              choices=LOAN_STATUS,
                              blank=True,
                              default='m',
                              help_text=_('Book availability'),
                              )
    borrower = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def is_overdue(self):
        """Determines if the book is overdue based on due date and current date."""
        return bool(self.due_back and date.today() > self.due_back)

    class Meta:
        ordering = ['due_back']
        permissions = (("can_mark_returned", "Set book as returned"),)

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.id} ({self.book.title})'


class Author(models.Model):
    """Model representing an author."""
    first_name = models.CharField(_('first_name'), max_length=100)
    last_name = models.CharField(_('last_name'), max_length=100)
    date_of_birth = models.DateField(_('birth'), null=True, blank=True)
    date_of_death = models.DateField(_('died'), null=True, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.last_name}, {self.first_name}'


class RenewBookModelForm(ModelForm):
    def clean_due_back(self):
        data = self.cleaned_data['due_back']
        today = datetime.date.today()

        # Check if a date is not in the past.
        if data < today:
            raise ValidationError(_('Invalid date - renewal in past'))

        # Check if a date is in the allowed range (+4 weeks from today).
        if data > today + datetime.timedelta(weeks=4):
            raise ValidationError(
                _('Invalid date - renewal more than 4 weeks ahead'))

        # Remember to always return the cleaned data.
        return data

    class Meta:
        model = BookInstance
        fields = ['due_back']
        labels = {'due_back': _('Renewal date')}
        help_texts = {'due_back': _(
            'Enter a date between now and 4 weeks (default 3).')}
