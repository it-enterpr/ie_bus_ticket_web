/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";


const { markup } = owl;

publicWidget.registry.BusSearchPage = publicWidget.Widget.extend({
    selector: '#ie_bus_booking_detail_table',
    events: {
        'click .book_ticket': '_onClickBookTicket',
    },

    _onClickBookTicket: async function (ev) {
        var self = this
        var $btn = $(ev.currentTarget)
        var search_id = parseInt($btn.attr("data-id"));
        self.search_id = search_id
        var firstSeatLabel = 1;

        if (search_id) {

            var result = await rpc('/get_booked_seat',{
                'trip_id': search_id
            });

            var bigData = JSON.parse(result);
            var map_list = bigData["data"];
            var front_seating_map_class = ".front-seating-map-" + search_id;
            var counter_id = "#counter-" + search_id;
            var selected_seats_id = "#selected-seats-" + search_id;
            var total_id = "#total-" + search_id;
            var currency_symbol_id = "#currency_symbol_" + search_id;
            var legend = ".legend-" + search_id;
            var checkout_button_class = ".checkout-button-" + search_id;
            var go_button_class = ".go-button-" + search_id;
            var dropping_point_class = ".dropping-point_" + search_id;
            var boarding_point_class = ".boarding-point_" + search_id;
            var amenities_list_class = ".amenities_list_" + search_id;

            if (map_list.length > 0) {
                var $cart = $(selected_seats_id)
                var $counter = $(counter_id)
                var $total = $(total_id)
                var $currency_symbol = $(currency_symbol_id)

                var sc = $(front_seating_map_class).seatCharts({
                    map: map_list,
                    seats: bigData["seats"],

                    naming: {
                        top: false,
                        getLabel: function (character, row, column) {
                            return firstSeatLabel++;
                        },
                    },

                    legend: {
                        node: $(legend),
                        items: bigData["legend_items"],
                    },

                    click: function () {
                        if (this.status() == "available") {
                            var selected_seat = "R" + this.settings.id.split("_")[0] + " S" + this.settings.id.split("_")[1];
                            $(
                                "<li>" +
                                this.data().category +
                                " Seat # " +
                                "<b>" +
                                selected_seat +
                                ": $" +
                                this.data().price +
                                '</b> <a href="#" class="cancel-cart-item"><i class="fa fa-fw o_button_icon fa-close"></i></a></li>'
                            )
                                .attr("id", "cart-item-" + this.settings.id)
                                .data("seatId", this.settings.id)
                                .data("seatLabel", this.settings.label)
                                .data("seatPrice", this.data().price)
                                .data("seatCateg", this.data().category)
                                .appendTo($cart);

                            $counter.text(sc.find("selected").length + 1);
                            $total.text(self.recalculateTotal(sc) + this.data().price);
                            $(checkout_button_class).removeAttr("disabled");
                            return "selected";
                        } else if (this.status() == "selected") {
                            //update the counter
                            $counter.text(sc.find("selected").length - 1);
                            //and total
                            $total.text(self.recalculateTotal(sc) - this.data().price);

                            //remove the item from our cart
                            $("#cart-item-" + this.settings.id).remove();

                            if (sc.find("selected").length <= 1) {
                                $(checkout_button_class).attr("disabled", "disabled");
                            }
                            return "available";
                        } else if (this.status() == "unavailable") {
                            //seat has been already booked
                            return "unavailable";
                        } else {
                            return this.style();
                        }
                    }

                })

                sc.get(bigData["booked_seat"]).status("unavailable");

                $(selected_seats_id).on("click", ".cancel-cart-item", function () {
                    sc.get($(this).parents("li:first").data("seatId")).click();
                });

                if (bigData["boarding_points"].length > 0) {
                    var boarding_html_data =
                        '<div class="row" style="align-items: center;"><div class="col-lg-4 col-md-12 col-sm-12 col-12 pl-8 pr-0"><h5 class="bp_text">Boarding Point :</h5></div><div class="col-lg-8 col-md-12 col-sm-12 col-12 pl-0"> <select required="required" id="boarding_point">';
                    $.each(bigData["boarding_points"], function (key, value) {
                        boarding_html_data += '<option value="' + value[0] + '">' + value[1] + "</option>";
                    });
                    boarding_html_data += '</select></span></div></div>';
                    $(boarding_point_class).html(boarding_html_data);
                }

                if (bigData["dropping_points"].length > 0) {
                    var dropping_html_data =
                        '<div class="row" style="align-items: center;"><div class="col-lg-4 col-md-12 col-sm-12 col-12 pl-8 pr-0"><h5 class="dp_text">Dropping Point :</h5></div><div class="col-lg-8 col-md-12 col-sm-12 col-12 pl-0"> <select required="required" id="dropping_point">';
                    $.each(bigData["dropping_points"], function (key, value) {
                        dropping_html_data += '<option value="' + value[0] + '">' + value[1] + "</option>";
                    });
                    dropping_html_data += '</select></span></div></div>';
                    $(dropping_point_class).html(dropping_html_data);
                }

                if (bigData["amenities_list"].length > 0) {
                    var amenities_html_data =
                        '<div class="row"><div class="col-lg-4 col-md-12 col-sm-12 col-12 pl-8 pr-0"><h5 class="am_text">Amenities :</h5></div><div class="col-lg-8 col-md-12 col-sm-12 col-12 pl-0" id="bus_amenities">';
                    $.each(bigData["amenities_list"], function (key, value) {
                        amenities_html_data += '<span class="amenities_tag">' + value[0] + "</span>";
                    });
                    amenities_html_data += "</div></div>";
                    $(amenities_list_class).html(amenities_html_data);
                }

            }

            $('body').find(checkout_button_class).on("click", self._onClickrCheckoutbutton.bind(self, search_id, selected_seats_id, go_button_class));
            $('body').find(go_button_class).on("click", self._onClickrGoButton.bind(self, selected_seats_id));

        }
    },

    recalculateTotal: function (sc) {
        var total = 0;
        sc.find("selected").each(function () {
            total += this.data().price;
        });
        return total;
    },


    _onClickrCheckoutbutton: function (self, selected_seats_id, go_button_class) {
        var passenger_info_class = ".passenger_info_" + this.search_id;
        var passenger_detail_class = ".passenger-detail_" + this.search_id;

        $(passenger_info_class).css("visibility", "visible");
        $(go_button_class).css("visibility", "visible");

        // var self = this
        var seat_list = [];
        var html_data = "";

        var i = 1;



        $('.selected-seats').find('li').each(function (index) {

            seat_list.push($(this).data("seatId"));
            html_data += "<tr>";
            html_data += '<td ><span class="p_counter">' + i + ".</span></td>";
            html_data += '<td><input required="required" type="text" class="mtb-10" name="p_name_' + i + '"></input></td>';
            html_data += '<td><input required="required" type="text" class="mtb-10" name="p_email_' + i + '"></input></td>';
            html_data += '<td><input required="required" type="number" class="mtb-10" style="width:50%"  min="0" max="100" name="p_age_' + i + '"></input></td>';
            html_data += '<td><select class="mtb-10" name="p_gender_' + i + '"><option value="Male">Male</option><option value="Female">Female</option><option value="Child">Children</option></select></td>';
            html_data += "</tr>";
            i += 1;
        });

        $(passenger_detail_class).html(html_data);

    },

    _onClickrGoButton: async function (self, selected_seats_id) {
        var data_list = [];
        var i = 1;
        var count = false;
        var self = this;

        $('.selected-seats').find("li").each(function (index) {

            if (count == false) {
                var seat_list = [];

                seat_list.push($(this).data("seatId"));
                seat_list.push($(this).data("seatLabel"));
                seat_list.push($(this).data("seatPrice"));


                var name_input = "input[name='p_name_" + i + "']";
                var email_input = "input[name='p_email_" + i + "']";
                var age_input = "input[name='p_age_" + i + "']";
                var gender_input = "select[name='p_gender_" + i + "']";
                var boarding_point = $("#boarding_point").val() || "";
                var dropping_point = $("#dropping_point").val() || "";

                if ($(name_input).val() == "" || $(email_input).val() == "" || $(age_input).val() == "" || $(gender_input).val() == "") {
                    alert("Please Enter Details !");
                    count = true;
                } else {
                    seat_list.push($(name_input).val());
                    seat_list.push($(email_input).val());
                    seat_list.push($(age_input).val());
                    seat_list.push($(gender_input).val());

                    seat_list.push(boarding_point);
                    seat_list.push(dropping_point);

                    data_list.push(seat_list);

                    i += 1;
                }
            }

        });

        if (count == false) {
            
            var result = await rpc('/add_cart_ticket',{
                'data_list': JSON.stringify(data_list),
                'search_trip_id': JSON.stringify(self.search_id )
            });
            location.href = "/shop/cart";
        }
    }

});
