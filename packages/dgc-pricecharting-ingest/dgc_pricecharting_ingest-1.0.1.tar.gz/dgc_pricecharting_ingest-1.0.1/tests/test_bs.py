import pytest
from dgc_pricecharting_ingest.bs import extract_pricecharting_id, extract_image_info, extract_card_number


def test_extracts_numeric_id():
    html = """
    <div id="full_details">
      <table id="attribute">
        <tr>
          <td class="title">PriceCharting ID:</td>
          <td class="details">7307259</td>
        </tr>
      </table>
    </div>
    """
    assert extract_pricecharting_id(html) == "7307259"


def test_returns_none_when_no_full_details():
    # PriceCharting ID exists on the page but NOT inside #full_details -> must return None (no fallback)
    html = """
    <div id="other">
      <table>
        <tr>
          <td class="title">PriceCharting ID:</td>
          <td class="details">999999</td>
        </tr>
      </table>
    </div>
    <div id="full_details">
      <p>some other content</p>
    </div>
    """
    assert extract_pricecharting_id(html) is None


def test_returns_none_when_title_has_no_sibling_details_td():
    html = """
    <div id="full_details">
      <table>
        <tr>
          <td class="title">PriceCharting ID:</td>
          <!-- no sibling details td -->
        </tr>
      </table>
    </div>
    """
    assert extract_pricecharting_id(html) is None


def test_returns_none_when_details_contains_no_digits():
    html = """
    <div id="full_details">
      <table>
        <tr>
          <td class="title">PriceCharting ID:</td>
          <td class="details">none</td>
        </tr>
      </table>
    </div>
    """
    assert extract_pricecharting_id(html) is None


def test_extracts_first_numeric_token_from_mixed_text():
    html = """
    <div id="full_details">
      <table>
        <tr>
          <td class="title">PriceCharting ID:</td>
          <td class="details">ref: abc123 def456</td>
        </tr>
      </table>
    </div>
    """
    # first numeric token is "123"
    assert extract_pricecharting_id(html) == "123"


def test_matches_case_and_whitespace_variants():
    html = """
    <div id="full_details">
      <table>
        <tr>
          <td class="title">  PriceCharting   ID  </td>
          <td class="details">  98765  </td>
        </tr>
      </table>
    </div>
    """
    assert extract_pricecharting_id(html) == "98765"


def test_multiple_pricecharting_rows_returns_first_found():
    html = """
    <div id="full_details">
      <table>
        <tr>
          <td class="title">PriceCharting ID:</td>
          <td class="details">111 222</td>
        </tr>
        <tr>
          <td class="title">PriceCharting ID:</td>
          <td class="details">333</td>
        </tr>
      </table>
    </div>
    """
    # function searches in document order and returns the first numeric match
    assert extract_pricecharting_id(html) == "111"


def test_extract_card_number_with_hash():
    html = """
    <div id="full_details">
      <table>
        <tr><td class="title">Card Number:</td><td>#123</td></tr>
      </table>
    </div>
    """
    assert extract_card_number(html) == "123"


def test_extract_card_number_without_hash():
    html = """
    <div id="full_details">
      <table>
        <tr><td class="title">Card Number:</td><td>ST09-001</td></tr>
      </table>
    </div>
    """
    assert extract_card_number(html) == "ST09-001"


def test_extract_card_number_with_spaces():
    html = """
    <div id="full_details">
      <table>
        <tr><td class="title">  Card Number  </td><td>   #45   </td></tr>
      </table>
    </div>
    """
    assert extract_card_number(html) == "45"


def test_extract_card_number_no_hash_no_trim_needed():
    html = """
    <div id="full_details">
      <table>
        <tr><td class="title">Card Number:</td><td>ABC-999</td></tr>
      </table>
    </div>
    """
    assert extract_card_number(html) == "ABC-999"


def test_extract_card_number_no_full_details():
    html = "<html><body><p>No details here</p></body></html>"
    assert extract_card_number(html) is None


def test_extract_card_number_no_matching_title():
    html = """
    <div id="full_details">
      <table>
        <tr><td class="title">PriceCharting ID:</td><td>#888</td></tr>
      </table>
    </div>
    """
    assert extract_card_number(html) is None


def test_extract_card_number_empty_value():
    html = """
    <div id="full_details">
      <table>
        <tr><td class="title">Card Number:</td><td></td></tr>
      </table>
    </div>
    """
    assert extract_card_number(html) is None

def test_extract_card_number_with_linebreaks():
    html = """
    <div id="full_details">
      <table>
        <tr>
            <td class="title">Card Number:</td>
            <td class="details" itemprop="model-number">
                
                    #34
                
            
                
            
            </td>
        </tr>
      </table>
    </div>
    """
    assert extract_card_number(html) == "34"

@pytest.mark.parametrize("image_id, size", [
    ("abc123xyz", 240),
    ("testid987", 600),
    ("id180", 180),
])
def test_extract_image_info_valid_images(image_id, size):
    html = f'''
    <div id="product_details">
      <div class="cover">
        <a>
          <img src="https://storage.googleapis.com/images.pricecharting.com/{image_id}/{size}.jpg">
        </a>
      </div>
    </div>
    '''
    info = extract_image_info(html)
    assert info is not None
    assert info["image_id"] == image_id
    assert info["no_image"] is False

# ---------------------------
# Placeholder / no image
# ---------------------------
def test_extract_image_info_placeholder_no_image():
    html = '''
    <div id="product_details">
      <div class="cover">
        <a>
          <img src="/images/no-image-available.png">
        </a>
      </div>
    </div>
    '''
    info = extract_image_info(html)
    assert info is not None
    assert info["image_id"] is None
    assert info["no_image"] is True

# ---------------------------
# Missing <img> tag
# ---------------------------
def test_extract_image_info_missing_img_tag():
    html = '<div id="product_details"><div class="cover"></div></div>'
    info = extract_image_info(html)
    assert info is not None
    assert info["image_id"] is None
    assert info["no_image"] is False

# ---------------------------
# Unexpected src (external URL)
# ---------------------------
def test_extract_image_info_unexpected_src():
    html = '''
    <div id="product_details">
      <div class="cover">
        <a>
          <img src="https://cdn.example.com/images/foo.png">
        </a>
      </div>
    </div>
    '''
    info = extract_image_info(html)
    assert info is not None
    assert info["image_id"] is None
    assert info["no_image"] is False

# ---------------------------
# Missing product_details div
# ---------------------------
def test_extract_image_info_missing_product_div():
    html = '<div><a><img src="https://storage.googleapis.com/images.pricecharting.com/xyz/240.jpg"></a></div>'
    info = extract_image_info(html)
    assert info is None

# ---------------------------
# Missing src attribute
# ---------------------------
def test_extract_image_info_missing_src_attribute():
    html = '''
    <div id="product_details">
      <div class="cover">
        <a><img></a>
      </div>
    </div>
    '''
    info = extract_image_info(html)
    assert info is not None
    assert info["image_id"] is None
    assert info["no_image"] is False