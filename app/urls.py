from app import controllers, app

app.add_url_rule('/', 'index', controllers.index)
app.add_url_rule('/cart', 'cart', controllers.cart)
app.add_url_rule('/login', 'login', controllers.login)
app.add_url_rule('/logout', 'logout', controllers.logout)
app.add_url_rule('/register', 'register', controllers.register)
app.add_url_rule('/my_orders', 'my-orders', controllers.my_orders)
app.add_url_rule('/my_orders/<int:order_id>', 'my-order-details', controllers.my_order_details)
app.add_url_rule('/payment', 'payment', controllers.payment)
app.add_url_rule('/vnpay_return', 'vnpay-return', controllers.vnpay_return)
app.add_url_rule('/sales', 'sales', controllers.sales)
app.add_url_rule('/sales/login', 'staff-login', controllers.staff_login, methods=['POST', 'GET'])
app.add_url_rule('/sales/logout', 'staff-logout', controllers.staff_logout)
app.add_url_rule('/api/sales', 'api-sales-cart', controllers.add_to_sales_cart, methods=['POST'])
app.add_url_rule('/api/sales/<string:book_id>', 'update-sales-cart', controllers.update_sales_cart,
                 methods=['PUT', 'DELETE'])
app.add_url_rule('/invoice', 'pay_invoice', controllers.pay_invoice, methods=['POST'])
app.add_url_rule('/invoice/print/<int:receipt_id>', 'print_invoice', controllers.print_invoice, methods=['POST', 'GET'])
app.add_url_rule('/books/<int:book_id>', 'book-details', controllers.details)
app.add_url_rule('/login', 'user-login', controllers.user_login, methods=['POST', 'GET'])
app.add_url_rule('/register', 'user-register', controllers.user_register, methods=['POST', 'GET'])
app.add_url_rule('/admin/login', 'admin-login', controllers.admin_login, methods=['POST', 'GET'])
app.add_url_rule('/admin/logout', 'admin-logout', controllers.admin_logout)
app.add_url_rule('/admin/edit_rules', 'edit-rules', controllers.edit_rules, methods=['POST'])
app.add_url_rule('/api/cart', 'api-cart', controllers.add_to_cart, methods=['POST'])
app.add_url_rule('/api/cart/<string:book_id>', 'update-cart', controllers.update_cart, methods=['PUT'])
app.add_url_rule('/api/cart/<string:book_id>', 'delete-cart', controllers.delete_cart, methods=['DELETE'])
app.add_url_rule('/api/pay', 'pay', controllers.pay, methods=['POST'])
app.add_url_rule('/api/books/<int:book_id>/comments', 'comments', controllers.comments)
app.add_url_rule('/api/books/<int:book_id>/comments', 'add-comment', controllers.add_comment, methods=['POST'])
app.add_url_rule('/sendotp', 'sendotp', controllers.send_otp, methods=['SEND'])
