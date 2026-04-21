from parsers.site_parser import SiteParser


def test_site_parser_supports_generic_parse_without_rule():
    parser = SiteParser([])
    html = """
    <html>
      <head>
        <meta property="og:title" content="通用识别商品" />
        <meta property="product:price:amount" content="29.90" />
      </head>
      <body>
        <div class="promo-text">限时优惠</div>
      </body>
    </html>
    """

    result = parser.parse("https://unknown.example.com/item/1", html)

    assert result["site_name"] == "unknown.example.com"
    assert result["product_name"] == "通用识别商品"
    assert result["current_price"] == 29.9
    assert result["promotion_text"] == "限时优惠"
    assert result["matched_rule"] == "通用识别"
    assert result["raw_extract"]["matched_selectors"]["name"] == "meta[property='og:title']"
    assert result["raw_extract"]["matched_selectors"]["current_price"] == "meta[property='product:price:amount']"
