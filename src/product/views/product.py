from django.core.paginator import Paginator
from django.views import generic

from product.models import Variant, Product, ProductVariantPrice, ProductVariant


class CreateProductView(generic.TemplateView):
    template_name = 'products/create.html'

    def get_context_data(self, **kwargs):
        context = super(CreateProductView, self).get_context_data(**kwargs)
        variants = Variant.objects.filter(active=True).values('id', 'title')
        context['product'] = True
        context['variants'] = list(variants.all())
        return context


class ProductListView(generic.ListView):
    template_name = 'products/list.html'
    paginate_by = 10  # Set the number of products to display per page

    def get_queryset(self):
        queryset = Product.objects.all()
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        product_list_data = []

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

        context["products"] = page_obj
        context["product_data"] = product_list_data
        context["pagination_details"] = self.get_pagination_details(page_obj)
        return context

    def get_pagination_details(self, page_obj):
        start_index = (page_obj.number - 1) * self.paginate_by + 1
        end_index = start_index + len(page_obj) - 1
        total_count = page_obj.paginator.count

        return f"Showing {start_index} to {end_index} out of {total_count}"