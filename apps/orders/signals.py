# stocks = order_models.FacturationStock.objects.filter(
#     facturation=billing
# )

# # Update quantity of each product in stock for each batch in the facturation
# for facturation_stock in stocks:
#     stock = facturation_stock.stock
#     stock.quantity -= facturation_stock.quantity
#     stock.save()
