# -*- coding: utf-8 -*-
# IT Enterprise.

from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def get_portal_movie_url(self, suffix=None, report_type=None, download=None, query_string=None, anchor=None):
        """
            Get a portal url for this model, including access_token.
            The associated route must handle the flags for them to have any effect.
            - suffix: string to append to the url, before the query string
            - report_type: report_type query string, often one of: html, pdf, text
            - download: set the download query string to true
            - query_string: additional query string
            - anchor: string to append after the anchor #
        """
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')

        url = base_url+'/my/bus_ticket/' + \
            str(self.id)+'?'+'access_token'+'=' + \
            self.access_token+'&report_type=pdf&download=true'
        return url
