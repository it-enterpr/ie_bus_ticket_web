# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

{
    "name": "Bus Tickets Website",

    "author": "IT Enterprise",

    "website": "https://www.it-enterprise.solutions",

    "support": "support@it-enterprise.cz", 

    "version": "0.0.1",

    "category": "Website",

    "license": "OPL-1",

    "summary": "Module Bus Ticket Booking  ",

    "description": """Are you looking for a bus tickets booking management system on odoo? Here it is. We build an application for bus management. In this application, we will provide features like Ticket Booking from Website, Bus Management, Ticket Booking (Backend), Route Management, Special Price for Special Route, Trip Management, Real-Time Check-In, and so on.""",

    'depends': [
        'ie_bus_ticket_admin',
        'website_sale'
    ],

    'data': [
        # 'views/assets.xml',
        'views/ie_website_bus_booking_templates.xml',
        'views/sale_portal_template.xml',
        'data/ie_website_bus_booking_data.xml',

    ],

    'assets': {

        'web.assets_frontend': [

            "ie_bus_ticket_web/static/src/js/jquery.seat-charts.js",
            "ie_bus_ticket_web/static/src/css/jquery.seat-charts.css",
            "ie_bus_ticket_web/static/src/scss/busbooking.scss",
            "ie_bus_ticket_web/static/src/scss/owl.carousel.css",
            "ie_bus_ticket_web/static/src/scss/owl.theme.default.min.css",
            "ie_bus_ticket_web/static/src/js/ie_seat_booking.js",
            "ie_bus_ticket_web/static/src/js/window_scroll.js",
            "ie_bus_ticket_web/static/src/js/owl.carousel.js",
            # "https://code.jquery.com/ui/1.12.1/jquery-ui.js",


        ],
    },

    'demo': [

    ],
    "images": ["static/description/background.png", ],
    # 'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
    "price": 770.0,
    "currency": "EUR"
}
