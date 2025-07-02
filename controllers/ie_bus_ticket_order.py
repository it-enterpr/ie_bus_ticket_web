# -*- coding: utf-8 -*-
# IT Enterprise.

import json
from datetime import date
from odoo import  http
from odoo import _
from odoo.http import request
from datetime import datetime
from odoo.tools.safe_eval import safe_eval
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.sale.controllers.portal import CustomerPortal


class ShDownloadBusTicketPDF(CustomerPortal):
    @http.route(['/my/bus_ticket/<int:saleorder_id>'], type='http', auth="public", website=True)
    def portal_my_bus_ticket_download(self, saleorder_id, access_token=None, download=False, **kw):

        saleorder = request.env['sale.order'].sudo().browse(saleorder_id)
        if saleorder.access_token == access_token:
            saleorder_sudo = self._document_check_access(
                'sale.order', saleorder_id, access_token)
            return self._show_report(model=saleorder_sudo, report_type='pdf', report_ref='ie_bus_admin.ticket_report', download=download)
        else:
            return request.redirect('/')


class WebsiteSale(WebsiteSale):

    @http.route('/shop/payment/validate', type='http', auth="public", website=True, sitemap=False)
    def shop_payment_validate(self, sale_order_id=None, **post):
        result = super(WebsiteSale,self).shop_payment_validate(sale_order_id=sale_order_id,post=post)

        if sale_order_id is None:
            order = request.website.sale_get_order()
            if not order and 'sale_last_order_id' in request.session:
                # Retrieve the last known order from the session if the session key `sale_order_id`
                # was prematurely cleared. This is done to prevent the user from updating their cart
                # after payment in case they don't return from payment through this route.
                last_order_id = request.session['sale_last_order_id']
                order = request.env['sale.order'].sudo().browse(last_order_id).exists()
        else:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            assert order.id == request.session.get('sale_last_order_id')

        if order and order.trip_id and order.invoice_status == 'invoiced':
            for line in order.order_line:
                line.write({'booking_status': 'confirm'})
                if line.seat:
                    request.env['bus.booked.seat'].sudo().create({'bus_id': order.trip_id.id,
                                                                'name': line.seat,
                                                                'seat_id': line.seat_id
                                                                })

        return result

    @http.route(['/shop/print'], type='http', auth="public", website=True, sitemap=False)
    def print_saleorder(self, **kwargs):
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            # pdf, _ = request.env.ref('ie_bus_admin.ticket_report').sudo()._render_qweb_pdf([sale_order_id])
            pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf("ie_bus_admin.ticket_report", sale_order_id)[0]
            pdfhttpheaders = [('Content-Type', 'application/pdf'),
                              ('Content-Length', u'%s' % len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        else:
            return request.redirect('/shop')

    @http.route(['/shop/cart'], type='http', auth="public", website=True)
    def cart(self, **post):
        res = super(WebsiteSale, self).cart(**post)
        # ------------------------------------------------------------------
        # SET SEARCH RESULT PRICE IN SALE ORDER LINE AS PER BACKEND RECORD
        # ------------------------------------------------------------------
        order = request.website.sale_get_order()
        if order:
            get_bus_booking_lines = order.order_line.filtered(lambda m: m.search_id)
            if get_bus_booking_lines:
                for line in get_bus_booking_lines:
                    search_rec = request.env['ie.bus.search.result'].sudo().browse(line.search_id.id)
                    line.price_unit = search_rec.price
        # ------------------------------------------------------------------
        # SET SEARCH RESULT PRICE IN SALE ORDER LINE AS PER BACKEND RECORD
        # ------------------------------------------------------------------
        return res

    @http.route()
    def shop_payment(self, **post):
        # ------------------------------------------------------------------
        # SET SEARCH RESULT PRICE IN SALE ORDER LINE AS PER BACKEND RECORD
        # ------------------------------------------------------------------
        order = request.website.sale_get_order()
        if order:
            get_bus_booking_lines = order.order_line.filtered(lambda m: m.search_id)
            if get_bus_booking_lines:
                for line in get_bus_booking_lines:
                    search_rec = request.env['ie.bus.search.result'].sudo().browse(line.search_id.id)
                    line.price_unit = search_rec.price
        # ------------------------------------------------------------------
        # SET SEARCH RESULT PRICE IN SALE ORDER LINE AS PER BACKEND RECORD
        # ------------------------------------------------------------------
        res = super(WebsiteSale, self).shop_payment(**post)
        return res

class BusTicketFlow(http.Controller):

    @http.route(['/add_cart_ticket'], type='json', auth='public', website=True)
    def next_checkout(self, **post):
        trip_id = False
        if post.get('search_trip_id'):
            search_id = request.env['ie.bus.search.result'].sudo().browse(
                int(post.get('search_trip_id')))
            if search_id and search_id.trip_id:
                trip_id = search_id.trip_id.id

        if post.get('data_list'):

            passenger_detail = post.get('data_list')
            count = 0
            sale_order = False
            for passenger in safe_eval(passenger_detail):
                if count == 0:

                    partner = request.env['res.partner'].sudo().search(
                        [('email', '=', str(passenger[4]))], limit=1)
                    if not partner:
                        partner = request.env['res.partner'].sudo().create({'name': str(passenger[3]),
                                                                            'email': str(passenger[4]),
                                                                            'type': 'passenger',
                                                                            })

                    sale_order = request.env['sale.order'].sudo().create(
                        {'partner_id': partner.id, 'trip_id': trip_id})

                    product = request.env['product.product'].sudo().search(
                        [('default_code', '=', 'ticket'), ('is_published', '=', True)], limit=1)
                    if not product:
                        product = request.env['product.product'].sudo().create({'default_code': 'ticket',
                                                                                'name': 'Bus Ticket',
                                                                                'type': 'service',
                                                                                'is_published': True
                                                                                })

                    order_line_vals = {'product_id': product.id,
                                       'name': product.name,
                                       'product_uom_qty': 1.0,
                                       'price_unit': float(passenger[2]),
                                       'order_id': sale_order.id,
                                       'seat': str(passenger[1]),
                                       'seat_id': str(passenger[0]),
                                       'p_name': str(passenger[3]),
                                       'p_email': str(passenger[4]),
                                       'p_age': str(passenger[5]),
                                       'p_gender': str(passenger[6]),
                                       'boarding_point': str(passenger[7]),
                                       'dropping_point': str(passenger[8]),
                                       'trip_id': trip_id,
                                       'search_id': search_id.id
                                       }
                    request.env['sale.order.line'].sudo().create(
                        order_line_vals)

                    count = 1
                else:
                    if sale_order:
                        product = request.env['product.product'].sudo().search(
                            [('default_code', '=', 'ticket'), ('is_published', '=', True)], limit=1)
                        if not product:
                            product = request.env['product.product'].sudo().create({'default_code': 'ticket',
                                                                                    'name': 'Bus Ticket',
                                                                                    'type': 'service',
                                                                                    'is_published': True
                                                                                    })

                        order_line_vals = {'product_id': product.id,
                                           'name': product.name,
                                           'product_uom_qty': 1.0,
                                           'price_unit': float(passenger[2]),
                                           'order_id': sale_order.id,
                                           'seat': str(passenger[1]),
                                           'seat_id': str(passenger[0]),
                                           'p_name': str(passenger[3]),
                                           'p_email': str(passenger[4]),
                                           'p_age': str(passenger[5]),
                                           'p_gender': str(passenger[6]),
                                           'boarding_point': str(passenger[7]),
                                           'dropping_point': str(passenger[8]),
                                           'trip_id': trip_id,
                                           'search_id': search_id.id
                                           }

                        # other contact as partner
                        request.env['res.partner'].sudo().create({
                            'type': 'passenger',
                            'parent_id': partner.id,
                            'name': str(passenger[3]),
                            'email': str(passenger[4]),
                        })

                        request.env['sale.order.line'].sudo().create(
                            order_line_vals)

        base_url = request.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        if sale_order:
            request.session['sale_order_id'] = sale_order.id

        bigData = {
            'id': sale_order.id,
            'base_url': base_url
        }

        return json.dumps(bigData)

    # @http.route(['''/get_booked_seat'''], type='http', auth="public", website=True, csrf=False)
    @http.route(['/get_booked_seat'], type='json', auth='public', website=True)
    def get_booked_seat_data(self, trip_id):

        trip_obj = request.env['ie.bus.search.result'].sudo().browse(
            int(trip_id))
        data = []
        seats = {}
        legend_items = []
        ticket_type_list = ['0', 'a', 'b', 'c', 'd', 'e',
                            'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o']
        if trip_obj.bus_id and trip_obj.bus_id.fleet_type:
            bus_type_obj = trip_obj.bus_id.fleet_type
            price = trip_obj.price
            max_cols = bus_type_obj.col_count
            i = 1
            seats[ticket_type_list[i]] = {
                'price': price, 'classes': ticket_type_list[i]+'-class', 'category': 'Standard'}
            legend_items.append([ticket_type_list[i], 'available', 'Standard'])
            for row in range(bus_type_obj.row_count):
                if bus_type_obj.layout == '2-2':
                    seat_arrangement = 'aa_aa'
                    data.append(seat_arrangement)
                elif bus_type_obj.layout == '1-1':
                    seat_arrangement = 'a_a'
                    data.append(seat_arrangement)
                elif bus_type_obj.layout == '2-1':
                    seat_arrangement = 'aa_a'
                    data.append(seat_arrangement)
                elif bus_type_obj.layout == '1-2':
                    seat_arrangement = 'a_aa'
                    data.append(seat_arrangement)
                elif bus_type_obj.layout == '3-2':
                    seat_arrangement = 'aaa_aa'
                    data.append(seat_arrangement)
                elif bus_type_obj.layout == '2-3':
                    seat_arrangement = 'aa_aaa'
                    data.append(seat_arrangement)
        legend_items.append(['f', 'unavailable', 'Already Booked'])
        booked_seat_list = []

        if trip_obj and trip_obj.booked_seat_ids:
            for booked_seat in trip_obj.booked_seat_ids:
                booked_seat_list.append(booked_seat.seat_id)

        boarding_points = []
        dropping_points = []
        if trip_obj.bording_from and trip_obj.bording_from.point_ids:
            for point in trip_obj.bording_from.point_ids:
                boarding_points.append([point.id, point.name])
        if trip_obj.to and trip_obj.to.point_ids:
            for point in trip_obj.to.point_ids:
                dropping_points.append([point.id, point.name])

        amenities_list = []
        if trip_obj.bus_id.amenities_ids:
            for amenities in trip_obj.bus_id.amenities_ids:
                amenities_list.append([amenities.name])
        bigData = {
            'data': data,
            'seats': seats,
            'legend_items': legend_items,
            'booked_seat': booked_seat_list,
            'currency': request.env.user.company_id.currency_id.symbol,
            'boarding_points': boarding_points,
            'dropping_points': dropping_points,
            'amenities_list': amenities_list
        }

        return json.dumps(bigData)

    def serach_bus_frontend(self, from_location, to_location, date, fleet_type):
        if date and from_location and to_location:
            # date = datetime.strptime(date, "%m/%d/%Y").strftime("%Y-%m-%d")
            date = date
            domain = [('bording_from', '=', from_location)]

            if fleet_type:
                domain.append(
                    ('route_line.fleet_id.fleet_type', '=', int(fleet_type)))

            route_line_from = request.env['ie.route.line'].sudo().search(
                domain)
            # first check from location
            search_ids = []
            if route_line_from:
                for each_line in route_line_from:
                    rid = each_line.route_line.id
                    fleet_id = each_line.route_line.fleet_id.id
                    # get route id and check to location with higher id of that route line
                    route_line_to = request.env['ie.route.line'].sudo().search(
                        [('route_line', '=', rid), ('id', '>=', each_line.id), ('to', '=', to_location)])

                    if route_line_to:
                        # Bus is available
                        # check in bus trip
                        existing_trip = request.env['ie.bus.trip'].sudo().search([('route', '=', rid), ('trip_date', '=', date),
                                                                                  ('bus_id', '=', fleet_id)], limit=1)

                        if not existing_trip:
                            existing_trip = request.env['ie.bus.trip'].sudo().create({
                                'route': rid,
                                'trip_date': date,
                                'bus_id': fleet_id,

                            })

                        # check in bus search result
                        trips = request.env['ie.bus.search.result'].sudo().search([('route', '=', rid), ('trip_date', '=', date),
                                                                                   ('bus_id', '=',
                                                                                    fleet_id),
                                                                                   ('bording_from',
                                                                                    '=', from_location),
                                                                                   ('to', '=', to_location)])
                        if trips:
                            for trip in trips:
                                search_ids.append(trip)
                                if existing_trip.booked_seat_ids:
                                    for booked_seat_id in existing_trip.booked_seat_ids:
                                        search_bus_id = request.env['bus.booked.seat'].sudo().create({'search_id': trip.id,
                                                                                                      'name': booked_seat_id.name,
                                                                                                      'seat_id': booked_seat_id.seat_id
                                                                                                      })

                        else:
                            from_location_obj = request.env['ie.bus.point'].sudo().browse(
                                from_location)
                            to_location_obj = request.env['ie.bus.point'].sudo().browse(
                                to_location)
                            result = request.env['ie.bus.search.result'].sudo().create({
                                'route': rid,
                                'trip_date': date,
                                'trip_start_date': each_line.start_times,
                                'trip_end_date': route_line_to.end_times,
                                'bus_id': fleet_id,
                                'price': each_line.route_line.get_price(from_location_obj, to_location_obj),
                                'bording_from': from_location,
                                'to': to_location,
                                'trip_id': existing_trip.id
                            })
                            if existing_trip.booked_seat_ids:
                                for booked_seat_id in existing_trip.booked_seat_ids:
                                    search_bus_id = request.env['bus.booked.seat'].sudo().create({'search_id': result.id,
                                                                                                  'name': booked_seat_id.name,
                                                                                                  'seat_id': booked_seat_id.seat_id
                                                                                                  })

                            search_ids.append(result)

                return search_ids

    @http.route(['''/busBooking'''], type='http', auth="public", website=True)
    def EventSeatBooking(self, **kwargs):
        points = []
        edit_translations = False
        if 'edit_translations' in kwargs:
            edit_translations = True
        for point in request.env['ie.bus.point'].sudo().search([]):
            points.append(point)

        bus_types = []
        for bus_type in request.env['ie.bus.type'].sudo().search([]):
            bus_types.append(bus_type)
        if kwargs:
            search_date = ''
            search_ids = []
            if kwargs.get('start_point', False) and kwargs.get('end_point', False) and kwargs.get('date', False):
                fleet_type = False

                if kwargs.get('fleet_type'):
                    fleet_type = kwargs.get('fleet_type')

                search_ids = self.serach_bus_frontend(int(kwargs.get('start_point')), int(
                    kwargs.get('end_point')), kwargs.get('date'), fleet_type)

                search_date = kwargs.get('date')

            return request.render("ie_bus_ticket_web.website_bus_booking_template", {
                'edit_translations':edit_translations, 
                'points': points, 'to_points': points, 'bus_types': bus_types, 'main_form': False, 'search_ids': search_ids, 'from_loc': kwargs.get('start_point', False), 'to_loc': kwargs.get('end_point', False), 'fleet_type': kwargs.get('fleet_type', False), 'search_date': search_date})

        return request.render("ie_bus_ticket_web.website_bus_booking_template", {
            'edit_translations':edit_translations,
            'points': points, 'bus_types': bus_types, 'main_form': True})
