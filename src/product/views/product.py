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
                    variant_list = []
                    variant_id = variant["option"]
                    price = variant.get("price", None)
                    stock = variant.get("stock", None)
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


class UpdateProductView(generic.UpdateView):
    template_name = 'products/update.html'
    model = Product
    fields = ["title", "sku", "description"]

    def post(self, request, *args, **kwargs):
        pk = kwargs.get("pk", None)
        if not pk:
            return HttpResponseBadRequest("Invalid input")

        file_path = request.FILES.getlist("file_path")
        sku = request.POST.get("sku", None)
        variants = request.POST.get("variants", [])
        product_price_id = request.data.get("product_price_id", None)

        if Product.objects.filter(~Q(pk=pk), sku=sku).exists():
            return HttpResponseBadRequest("Product SKU already exists")

        product_obj = Product.objects.filter(pk=pk).first()
        all_product_variant = list(ProductVariant.objects.filter(product=product_obj).values_list('id', flat=True))
        variant_list = []
        variants = json.loads(variants) if len(variants) >= 1 else None

        product_form = ProductCreateForm(request.POST, instance=product_obj)
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
                        product_variant_obj = ProductVariant.objects.filter(**data).first()
                        if product_variant_obj:
                            variant_list.append(product_variant_obj)
                        else:
                            product_variant_form = ProductVariantCreateForm(data)
                            if product_variant_form.is_valid():
                                product_variant_obj = product_variant_form.save()
                                variant_list.append(product_variant_obj)
                        if product_variant_obj.id in all_product_variant:
                            all_product_variant.remove(product_variant_obj.id)
                    price = request.POST.get("price", None)
                    stock = request.POST.get("price", None)

                    # manage product price data
                    price_data = {
                        "product": product_obj,
                        "product_variant_one": variant_list[0] if len(variant_list) >= 1 else None,
                        "product_variant_two": variant_list[1] if len(variant_list) >= 2 else None,
                        "product_variant_three": variant_list[2] if len(variant_list) >= 3 else None,
                        "price": price if price else 0,
                        "stock": stock if stock else 0,
                    }
                    if product_price_id:
                        product_price_obj = ProductVariantPrice.objects.filter(pk=product_price_id).first()
                        product_price_form = ProductVariantPriceCreateForm(price_data, instance=product_price_obj)
                    else:
                        product_price_form = ProductVariantPriceCreateForm(price_data)
                        if product_price_form.is_valid():
                            product_price_form.save()
                    # remove not using variants
                    for variant_id in all_product_variant:
                        product_variant_obj = ProductVariant.objects.filter(pk=variant_id).first()
                        if product_variant_obj:
                            product_variant_obj.delete()

            return JsonResponse("Product updated", safe=False)
        else:
            return HttpResponseBadRequest("Invalid product data")

    def get_object(self):
        pk = self.kwargs.get("pk", None)
        if not pk:
            pass
        product_obj = Product.objects.get(pk=pk)
        return product_obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_price_variant_qs = ProductVariantPrice.objects.filter(product=context["object"])
        variant_list = []
        for product_price in product_price_variant_qs:
            variant_data = {
                "product_price_id": product_price.id,
                "product_variant_one": {
                    "id": product_price.product_variant_one.id,
                    "variant_title": product_price.product_variant_one.variant_title
                } if product_price.product_variant_one else "",

                "product_variant_two": {
                    "id": product_price.product_variant_two.id,
                    "variant_title": product_price.product_variant_two.variant_title
                } if product_price.product_variant_two else "",
                "product_variant_three": {
                    "id": product_price.product_variant_three.id,
                    "variant_title": product_price.product_variant_three.variant_title
                } if product_price.product_variant_three else "",
                "price": product_price.price,
                "stock": product_price.stock,
            }
            variant_list.append(variant_data)
        product_data = {
            "product_id": context["object"].id,
            "product_title": context["object"].title,
            "product_created_at": context["object"].created_at,
            "product_description": context["object"].description,
            "variant_data": variant_list
        }
        context["product"] = product_data
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
