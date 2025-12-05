import weasyprint
from django.conf import settings
from django.shortcuts import HttpResponse
from django.template.loader import render_to_string
from django.utils.text import slugify


# render to pdf
def render_pdf(request, html_path, context, output_filename):
    response = HttpResponse(content_type="application/pdf")

    # Ensure filename is safe
    filename = slugify(output_filename)
    response["Content-Disposition"] = f"attachment;filename={filename}.pdf"

    context["request"] = request
    html = render_to_string(html_path, context=context)

    stylesheets = [weasyprint.CSS(settings.STATIC_ROOT + "core/css/bulma.min.css")]
    weasyprint.HTML(string=html, base_url=request.build_absolute_uri()).write_pdf(
        response, stylesheets=stylesheets, presentational_hints=True
    )
    return response


def render_xlsx(request, resource, queryset, filename):
    dataset = resource.export(queryset=queryset)
    response = HttpResponse(dataset.xlsx, content_type=f"text/xlsx")
    response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
    return response
