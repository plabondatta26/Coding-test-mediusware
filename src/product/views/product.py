import json

from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.views import generic

from product.models import Variant, Product, ProductVariantPrice, ProductVariant
from product.forms import ProductCreateForm, ProductImageCreateForm, ProductVariantCreateForm, \
    ProductVariantPriceCreateForm


class CreateProductView(generic.TemplateView):
    template_name = 'products/create.html'

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        file_path = request.FILES.getlist("file_path")
        sku = request.POST.get("sku", None)
        variants = request.POST.get("variants", [])
        price = request.POST.get("price", None)
        stock = request.POST.get("price", None)

        if Product.objects.filter(sku=sku).exists():
            return HttpResponseBadRequest("Product SKU already exists")

        variant_list = []
        variants = json.loads(variants) if len(variants) >= 1 else None

        product_form = ProductCreateForm(request.POST)
        if product_form.is_valid():
            product_obj = product_form.save()

            # Manage product images
            for file in file_path:
                data = dict()
                data["file_path"] = file
                data["product"] = product_obj
                product_image_form = ProductImageCreateForm(data)
                if product_image_form.is_valid():
                    product_image_form.save()

            # Manage product variants
            if variants:
                for variant in variants:
                    variant_id = variant["option"]
                    for tag_name in variant["tags"]:
                        data = dict()
                        data["variant_title"] = tag_name
                        data["variant"] = Variant.objects.filter(pk=variant_id).first()
                        data["product"] = product_obj
                        product_variant_form = ProductVariantCreateForm(data)
                        if product_variant_form.is_valid():
                            product_variant_obj = product_variant_form.save()
                            variant_list.append(product_variant_obj)

            price_data = {
                "product": product_obj,
                "product_variant_one": variant_list[0] if len(variant_list) >= 1 else None,
                "product_variant_two": variant_list[1] if len(variant_list) >= 2 else None,
                "product_variant_three": variant_list[2] if len(variant_list) >= 3 else None,
                "price": price if price else 0,
                "stock": stock if stock else 0,
            }
            product_price_form = ProductVariantPriceCreateForm(price_data)
            if product_price_form.is_valid():
                product_price_form.save()
        else:
            return HttpResponseBadRequest("Invalid product data")
        return JsonResponse("Product created", safe=False)

    def get_context_data(self, **kwargs):
        context = super(CreateProductView, self).get_context_data(**kwargs)
        variants = Variant.objects.filter(active=True).values('id', 'title')
        context['product'] = True
        context['variants'] = list(variants.all())
        return context


class UpdateProductView(generic.TemplateView):
    template_name = 'products/create.html'

    def post(self, request, *args, **kwargs):
        pass

    def get_queryset(self):
        pk = self.kwargs.get("pk", None)
        if not pk:
            pass
        product_obj = Product.objects.filter(pk=pk).first()
        if not product_obj:
            pass
        return product_obj

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        product_obj = context["product_obj"]
        product_variant_qs = ProductVariantPrice.objects.filter(product=product_obj)
        variant_list = []
        for product_variant in product_variant_qs:
            variant_data = {
                "id": product_variant.id,
                "product_variant_one": product_variant.product_variant_one.variant_title
                if product_variant.product_variant_one else "",
                "product_variant_two": product_variant.product_variant_two.variant_title
                if product_variant.product_variant_two else "",
                "product_variant_three": product_variant.product_variant_three.variant_title
                if product_variant.product_variant_three else "",
                "price": product_variant.price,
                "stock": product_variant.stock,
            }
            variant_list.append(variant_data)
        product_data = {
            "product_id": product_obj.id,
            "product_title": product_obj.title,
            "product_created_at": product_obj.created_at,
            "product_description": product_obj.description,
            "variant_data": variant_list
        }
        context["product_obj"] = product_data
        return context


class ProductListView(generic.ListView):
    template_name = 'products/list.html'
    queryset = Product.objects.all()
    paginate_by = 10  # Set the number of products to display per page

    def get_queryset(self):
        queryset = Product.objects.all()
        # Retrieve filter parameters from the request
        title = self.request.GET.get('title', None)
        price_from = self.request.GET.get('price_from', None)
        price_to = self.request.GET.get('price_to', None)
        variant = self.request.GET.get('variant', None)
        date = self.request.GET.get('date', None)
        # Apply filters to the queryset
        if title:
            self.queryset = queryset.filter(title__icontains=title)

        # filter with price
        if price_from and price_to:
            product_variant_qs = ProductVariantPrice.objects.filter(price__range=[price_from, price_to]).values(
                'product')
            product_ids = []
            for variant_ids in product_variant_qs:
                if not variant_ids["product"] in product_ids:
                    product_ids.append(variant_ids["product"])
            self.queryset = queryset.filter(id__in=product_ids)

        # filter with color
        if variant:
            product_variant_qs = ProductVariantPrice.objects.filter(
                Q(product_variant_one__variant_title=variant) |
                Q(product_variant_two__variant_title=variant) |
                Q(product_variant_three__variant_title=variant)
            ).values(
                'product')
            product_ids = []
            for variant_ids in product_variant_qs:
                if not variant_ids["product"] in product_ids:
                    product_ids.append(variant_ids["product"])
            self.queryset = queryset.filter(id__in=product_ids)
        if date:
            self.queryset = queryset.filter(created_at__date=date)

        return self.queryset.distinct()

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        product_list_data = []
        variant_qs = ProductVariant.objects.all().values("variant_title").distinct()
        for product in context["product_list"]:
            product_variant_qs = ProductVariantPrice.objects.filter(product=product)
            variant_list = []
            for product_variant in product_variant_qs:
                variant_data = {
                    "product_variant_one": product_variant.product_variant_one.variant_title
                    if product_variant.product_variant_one else "",
                    "product_variant_two": product_variant.product_variant_two.variant_title
                    if product_variant.product_variant_two else "",
                    "product_variant_three": product_variant.product_variant_three.variant_title
                    if product_variant.product_variant_three else "",
                    "price": product_variant.price,
                    "stock": product_variant.stock,
                }
                variant_list.append(variant_data)
            product_data = {
                "product_id": product.id,
                "product_title": product.title,
                "product_created_at": product.created_at,
                "product_description": product.description,
                "variant_data": variant_list
            }
            product_list_data.append(product_data)

        paginator = Paginator(context["product_list"], self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context["variant_qs"] = variant_qs
        context["products"] = page_obj
        context["product_data"] = product_list_data
        context["pagination_details"] = self.get_pagination_details(page_obj, paginator)
        return context

    def get_pagination_details(self, page_obj, paginator):
        current_page = self.request.GET.get('page', 1)
        start_index = (int(current_page) - 1) * paginator.per_page + 1
        if paginator.count < 1:
            start_index = 0
        end_index = start_index + paginator.object_list.count() - 1
        if paginator.count < 1:
            end_index = 0
        return f"Showing {start_index} to {end_index} out of {self.queryset.count()}"
