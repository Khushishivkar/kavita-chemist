"""Shop details shown in the footer / contact page. Edit them here once."""


def shop(request):
    return {
        'SHOP': {
            'name': 'Kavita Chemist',
            'tagline': 'Your neighbourhood pharmacy, now with smarter stock control.',
            'address': 'Shop No. 1, Main Road, Mumbai, Maharashtra',
            'phone': '+91 00000 00000',
            'email': 'hello@kavitachemist.example',
            'hours': 'Mon - Sat: 9:00 AM - 9:00 PM',
        }
    }
