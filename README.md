# Mediusware Backend developer task

In this time I am fully focused backend  developer. For this reason it was challenged
to send data from React to Django. For that reason, I have solved this project for backend.
To do that I have replaced "TemplateView" and "UpdateView" to "APIView". And solve the problem.

## required documents
product create url: <a href="http://127.0.0.1:8000/product/create/"> http://127.0.0.1:8000/product/create/ </a><br>
Product create payload
```json
{
    "title":"test 1",
    "sku":105,
    "description":"This is description",
    "variants":[
        { 
            "option":1,
            "tags":["a", "B", "c"],
            "price":460,
            "stock":50
        },
        {
            "option":2,
            "tags":["1", "2", "3"],
            "price":461,
            "stock":51
        },{
            "option":3,
            "tags":["@", "#", "3"],
            "price":462,
            "stock":52
        }
        
    ]

}
```

Product update <a href="http://127.0.0.1:8000/product/update/1/"> http://127.0.0.1:8000/product/update/1/ </a><br>
Product Update payload
```json
{
    "title":"test 1",
    "sku":105,
    "description":"This is description",
    "variants":[
        { 
            "product_price_id":"46",
            "option":1,
            "tags":["a", "B", "c"],
            "price":460,
            "stock":50
        },
        {
            "product_price_id":"47",
            "option":2,
            "tags":["1", "2", "3"],
            "price":461,
            "stock":51
        },{
            "product_price_id":"48",
            "option":3,
            "tags":["@", "#", "3"],
            "price":462,
            "stock":52
        }
        
    ]

}
```