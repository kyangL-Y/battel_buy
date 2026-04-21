from parsers.site_parser import SiteParser


def test_parse_uses_json_ld_product_when_meta_selectors_missing():
    parser = SiteParser([])
    html = """
    <html>
      <head>
        <script type="application/ld+json">
          {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "JSON-LD 商品",
            "offers": {
              "@type": "Offer",
              "price": "88.60",
              "highPrice": "99.00"
            }
          }
        </script>
      </head>
      <body></body>
    </html>
    """

    result = parser.parse("https://unknown.example.com/item/1", html)

    assert result["product_name"] == "JSON-LD 商品"
    assert result["current_price"] == 88.6
    assert result["original_price"] == 99.0
    assert result["raw_extract"]["matched_selectors"]["name"] == "script[type='application/ld+json']"
    assert result["raw_extract"]["matched_selectors"]["current_price"] == "script[type='application/ld+json']"
