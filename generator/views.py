#!/usr/bin/env python
# -*- coding: utf-8 -*-
import glob
import os
import os.path
import tempfile

import pdfrw
from django.contrib.sessions.backends import file
from django.http import HttpResponse, StreamingHttpResponse

from django.shortcuts import render, redirect
from django.template import RequestContext
from django import forms
from pdfjinja import PdfJinja
import csv
import zipfile
from wsgiref.util import FileWrapper

# Create your views here.
from mailing.mailer import *

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


def relative_project_path(*x):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)


class FileChooser(forms.Form):
    csv = forms.Field(widget=forms.FileInput, label='Choose the CSV file that contains the data to fill the form',
                      required=True)
    pdf = forms.Field(widget=forms.FileInput, label='Choose the PDF form to be filled', required=True)
    form_fields = forms.CharField(label="Provide the name of the form fields to fill separated by commas (if >1)",
                                  max_length=255)

    def clean(self):
        cleaned_data = super(FileChooser, self).clean()
        csv_file = cleaned_data.get('csv')
        pdf_file = cleaned_data.get('pdf')
        form_fields = cleaned_data.get('form_fields')

        if csv_file and pdf_file:
            filename_csv = csv_file.name
            filename_pdf = pdf_file.name
            if not filename_csv.endswith('.csv') and not filename_pdf.endswith('.pdf'):
                raise forms.ValidationError("Files uploaded are not CSV and PDF respectively. "
                                            "Please upload proper file types")

        if csv_file:
            filename_csv = csv_file.name
            if not filename_csv.endswith('.csv'):
                raise forms.ValidationError("First file uploaded is not a CSV. Please upload only a CSV file")

        if pdf_file:
            filename_pdf = pdf_file.name
            if not filename_pdf.endswith('.pdf'):
                raise forms.ValidationError("Second file uploaded is not a PDF. Please upload only a PDf file")

        if not form_fields:
            raise forms.ValidationError("There are no form fields specified to fill")

        return file


def save_file(request, file, type):
    if file:
        path = relative_project_path('files')
        filename = request.FILES[type].name
        path_csv = path + '/'
        if not os.path.exists(path):
            os.makedirs(path_csv)
        file2save = path_csv + filename
        fout = open(file2save, 'wb+')
        for chunk in file.chunks():
            fout.write(chunk)
        fout.close()
        return file2save
    elif not file:
        return False


def fill_form_csvdata(pdf_file, csv_file, fields2fill):
    pdfForm = str(pdf_file)
    template_pdf = pdfrw.PdfReader(pdfForm)
    filled_forms_path = relative_project_path('files') + "/"
    counter = 0

    filled_forms_path = filled_forms_path.replace('\\', '*')
    filled_forms_path = filled_forms_path.replace('*', '/')


    with open(str(csv_file), 'rU', encoding="utf8", errors='ignore') as csvfile:
        csv_data = csv.reader(csvfile, delimiter=';')

        len_fields2fill = len(fields2fill)
        len_csv_columns = len(next(csv_data))
        if len_fields2fill is not len_csv_columns:
            return "Columns error"

        csvfile.seek(0)
        for row in csv_data:
            dict_temp = {}
            for x, i in enumerate(fields2fill):
                dict_temp[str(i)] = row[x]
                print(row[x])

            for page in template_pdf.pages:
                annotations = page['/Annots']
                for annotation in annotations:
                    if annotation['/Subtype'] == '/Widget':
                        if annotation['/T']:
                            key = annotation['/T'][1:-1]
                            if key in dict_temp.keys():
                                # Fill the PDF
                                annotation.update(
                                    pdfrw.PdfDict(V='{}'.format(dict_temp[key]))
                                )
                            # Lock the PDF form
                            annotation.update(pdfrw.PdfDict(Ff=1))
            template_pdf.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true')))
            pdfrw.PdfWriter().write(filled_forms_path + dict_temp['Name'] + '_teem.pdf', template_pdf)

            # Sends the email
            send_mail(dict_temp['Mail'], "TEEM'21", dict_temp['Name'], filled_forms_path + dict_temp['Name'] + '_teem.pdf')
            counter += 1

    return filled_forms_path


def serve_zip_clean(pdf_file, csv_file, filled_forms_path):
    temp = tempfile.TemporaryFile()
    zf = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
    files2zip_list = glob.glob(filled_forms_path + '*_teem.pdf')
    for file2zip in files2zip_list:
        try:
            zf.write(file2zip, os.path.basename(file2zip), zipfile.ZIP_DEFLATED)
        except:
            zf.close()
    zf.close()
    for file2zip in files2zip_list:
        os.remove(file2zip)
    os.remove(pdf_file)
    os.remove(csv_file)
    response = StreamingHttpResponse(FileWrapper(temp), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="pdf_forms_filled.zip"'
    response['Content-Length'] = temp.tell()
    temp.seek(0)
    return response


def clean_files():
    filled_forms_path = relative_project_path('files') + "/"
    files_list = glob.glob(filled_forms_path + '*')
    for file in files_list:
        os.remove(file)


def generate_files(request):
    if request.method == 'POST':
        form = FileChooser(request.POST, request.FILES)
        if form.is_valid():
            pdf_form = request.FILES['pdf']
            csv_file = request.FILES['csv']
            form_fields = request.POST.get('form_fields')

            file2save_pdf = save_file(request, pdf_form, "pdf")
            if not file2save_pdf:
                HttpResponse("Error uploading PDf file")
            file2save_csv = save_file(request, csv_file, "csv")
            if not file2save_csv:
                HttpResponse("Error uploading CSV file")

            form_fields = form_fields.replace(" ", "")
            fields2fill = form_fields.split(',')

            # Files uploaded properly, filling the PDF form & generating a new PDF per each CSV row
            filled_forms_path = fill_form_csvdata(file2save_pdf, file2save_csv, fields2fill)
            if filled_forms_path == "Columns error":
                clean_files()
                return HttpResponse("Error! Unable to fill PDF, number of CSV columns and number of fields to "
                                    "fill are not equal")
            elif filled_forms_path == "Filling error":
                clean_files()
                return HttpResponse("Error filling PDF forms. Please check the font type and other form fields "
                                    "configuration. Also check if there is enough disk space to generate all the PDFs")

            # PDFs generated properly. Offering the zip file donwload and removing all files uploaded and generated
            return serve_zip_clean(file2save_pdf, file2save_csv, filled_forms_path)

        else:
            # Form not valid. Show errors and try again
            return render(request, 'filechooser.html', locals())
    else:
        # Request method is not POST. Try again
        return render(request, 'filechooser.html', locals())


def index(request):
    form = FileChooser()
    return render(request, 'filechooser.html', locals())
