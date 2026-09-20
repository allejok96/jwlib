from jwlib.media._image_item import ItemWithImages
from jwlib.media.const import RATIOS_3_1, SIZES_FROM_SMALLEST, TAG_PREFER_SQUARE_IMAGES


def make_item(images: dict, tags=()):
    return ItemWithImages(images=images, tags=list(tags))


def test_get_image_no_images():
    item = make_item({})
    assert item.get_image() is None


def test_get_image_default_prefers_16_9():
    item = make_item({
        'sqr': {'lg': 'square.jpg'},
        'wss': {'lg': 'wide.jpg'},
    })
    assert item.get_image() == 'wide.jpg'


def test_get_image_prefers_square_when_tagged():
    item = make_item({
        'sqr': {'lg': 'square.jpg'},
        'wss': {'lg': 'wide.jpg'},
    }, tags=[TAG_PREFER_SQUARE_IMAGES])
    assert item.get_image() == 'square.jpg'


def test_get_image_default_size_is_largest_first():
    item = make_item({
        'wss': {'xs': 'tiny.jpg', 'lg': 'big.jpg'},
    })
    assert item.get_image() == 'big.jpg'


def test_get_image_falls_back_to_next_ratio_if_first_is_missing():
    item = make_item({
        'wss': {'lg': 'fallback.jpg'},
    })
    # Default ratios are RATIOS_16_9 = ('wsr', 'wss'); 'wsr' is missing entirely
    assert item.get_image() == 'fallback.jpg'


def test_get_image_falls_back_to_next_size_if_first_is_empty_string():
    item = make_item({
        'wsr': {'lg': '', 'sm': 'smaller.jpg'},
    })
    assert item.get_image(sizes=('lg', 'sm')) == 'smaller.jpg'


def test_get_image_explicit_ratios_and_sizes():
    item = make_item({
        'pnr': {'xs': 'banner-xs.jpg', 'lg': 'banner-lg.jpg'},
        'wss': {'lg': 'wide.jpg'},
    })
    assert item.get_image(ratios=RATIOS_3_1, sizes=SIZES_FROM_SMALLEST) == 'banner-xs.jpg'


def test_get_image_returns_none_when_no_ratio_matches():
    item = make_item({'sqr': {'lg': 'square.jpg'}})
    assert item.get_image(ratios=RATIOS_3_1) is None
