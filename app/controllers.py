import math
from flask import render_template, request, redirect, url_for, session, jsonify
from flask_login import logout_user, current_user, login_user, login_required
from flask_admin import expose
from app import dao, utils, app
from datetime import datetime


def index():
    kw = request.args.get('kw')
    cate_id = request.args.get('cate_id')
    page = request.args.get('page')
    page_size = app.config['PAGE_SIZE']

    books = dao.get_books(kw, cate_id, page)
    carousel_items = dao.get_carousel_items()

    num = dao.count_books()

    if kw or cate_id:
        num = len(books)
        return render_template('index.html', books=books, pages=math.ceil(num / page_size))
    if page:
        return render_template('index.html', books=books, pages=math.ceil(num / page_size))

    return render_template('index.html', books=books, amount=8, carousel_items=carousel_items,
                           index=True)


def cart():
    return render_template('cart.html')


def login():
    return render_template('login.html')


def logout():
    logout_user()
    return redirect(url_for('index'))


def register():
    return render_template('register.html')


def details(book_id):
    book = dao.get_book_by_id(book_id)
    authors = dao.get_authors_by_book_id(book_id)
    categories = dao.get_categories_by_book_id(book_id)
    comments = dao.get_comments(book_id)
    return render_template('details.html', book=book, authors=authors, b_categories=categories,
                           comments=comments)


@login_required
def my_orders():
    orders = utils.get_orders()
    summary = utils.get_orders_summary(orders)

    return render_template('my-orders.html', orders=orders, summary=summary)


@login_required
def my_order_details(order_id):
    order = utils.get_order_by_id(order_id)
    user = dao.get_user_by_id(current_user.id)

    return render_template('my-orders-details.html', order=order, user=user)


def sales():
    books = dao.get_books()

    return render_template('sales/index.html', books=books)


def staff_login():
    books = dao.get_books()
    customers = dao.get_customers()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = dao.auth_account(username, password, 'staff')
        try:
            from app.models import Staff
            staff = Staff.query.get(user.id)
        except Exception as e:
            print(e)
        if user:
            login_user(user)
            return render_template('/sales/index.html', books=books, customers=customers,
                                   user=dao.get_user_by_id(user.id))
        else:
            return render_template('/sales/index.html', books=books, err_msg=True)

    return render_template('/sales/index.html', books=books, customers=customers,
                           user=dao.get_user_by_id(current_user.id))


def staff_logout():
    logout_user()
    return redirect('/sales')


def admin_login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        user = dao.auth_account(username=username, password=password, type='admin')
        if user:
            login_user(user=user)
        else:
            return render_template('/admin/login.html', err_acc=True)

    return redirect('/admin')


@expose("/")
def admin_logout():
    logout_user()
    return redirect('/admin')


def user_login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        user = dao.auth_account(username=username, password=password, type='user')
        if user:
            login_user(user=user)

            return redirect(url_for(request.args.get('next', 'index')))
        else:
            return render_template('login.html', err_acc=True)

    return render_template('login.html')


def user_register():
    err_msg = ''
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        conf_password = request.form.get("confirm-password")
        first_name = request.form.get("first-name")
        last_name = request.form.get("last-name")
        gender = request.form.get("gender")
        birthday = request.form.get("birthday")
        phone = request.form.get("phone")
        address = request.form.get("address")
        email = request.form.get("email")

        from app.models import User
        if User.query.filter_by(username=username).first():
            err_msg = "Tên tài khoản đã tồn tại"
        elif password.strip() != conf_password.strip():
            err_msg = "Mật khẩu không khớp"
        else:
            from app.models import GenderType
            if gender == GenderType.FEMALE.__val__():
                avatar = 'avatar_female.png'
            else:
                avatar = 'avatar_male.png'

            try:
                dao.add_customer(username=username, password=password, first_name=first_name, last_name=last_name,
                                 gender=gender, birthday=birthday, address=address, phone=phone, email=email,
                                 avatar=avatar)

                return redirect(url_for('login'))
            except:
                err_msg = "Hệ thống đang lỗi! Vui lòng quay lại sau!"

    return render_template('register.html', err_msg=err_msg)


def add_to_cart():
    key = app.config['CART_KEY']
    cart = session.get(key)
    if cart is None:
        cart = {}

    data = request.json
    id = str(data.get("id"))

    if id in cart:  # sp da co trong gio
        cart[id]['quantity'] += 1
    else:  # san pham chua co trong gio
        cart[id] = {
            "id": id,
            "name": data.get("name"),
            "price": data.get("price"),
            "quantity": 1,
            "max_quantity": dao.get_book_inventory(id).quantity
        }

    session[key] = cart

    return jsonify(utils.count_cart(cart))


def update_cart(book_id):
    key = app.config['CART_KEY']
    cart = session.get(key)

    if cart and book_id in cart:
        cart[book_id]['quantity'] = int(request.json['quantity'])

    session[key] = cart

    return jsonify(utils.count_cart(cart))


def delete_cart(book_id):
    key = app.config['CART_KEY']
    cart = session.get(key)

    if cart and book_id in cart:
        del cart[book_id]

    session[key] = cart

    return jsonify(utils.count_cart(cart))


def add_to_sales_cart():
    key = app.config['SALES_KEY']
    cart = session.get(key)
    if cart is None:
        cart = {}

    data = request.json
    id = str(data.get("id"))
    if id in cart:
        cart[id]['quantity'] += 1
    else:
        cart[id] = {
            "id": id,
            "name": data.get("name"),
            "price": data.get("price"),
            "quantity": 1,
            "max_quantity": dao.get_book_inventory(id).quantity
        }
    session[key] = cart

    return jsonify(utils.count_sales_cart(cart))


def update_sales_cart(book_id):
    key = app.config['SALES_KEY']
    cart = session.get(key)

    if request.method == "PUT":
        if cart and book_id in cart:
            cart[book_id]['quantity'] = int(request.json['quantity'])
    else:
        if cart and book_id in cart:
            del cart[book_id]

    session[key] = cart

    return jsonify(utils.count_sales_cart(cart))


@login_required
def payment():
    return render_template('payment.html')


@login_required
def pay():
    key = app.config['CART_KEY']
    cart = session.get(key)
    method = request.form.get('payment')

    if cart:
        try:
            if int(method) == 3:
                dao.save_order(cart=cart, is_paid=True)
            elif int(method) == 4:
                dao.save_order(cart=cart)
        except Exception as ex:
            print(str(ex))
            return jsonify({"status": 500})
        else:
            del session[key]

    return redirect('/my_orders')


@login_required
def pay_invoice():
    key = app.config['SALES_KEY']
    cart = session.get(key)
    customer_id = request.form.get('customer')

    try:
        receipt = dao.save_receipt(cart, customer_id=customer_id, staff_id=current_user.id)
    except Exception as e:
        print(e)
        return jsonify({"status": 500})

    return render_template('sales/invoice.html', receipt=receipt,
                           customer=dao.get_user_by_id(customer_id))


@login_required
def print_invoice(receipt_id):
    key = app.config['SALES_KEY']
    cart = session.get(key)

    if int(receipt_id) == 0:
        try:
            if request.method == 'POST':
                dao.save_receipt(cart, customer_id=int(request.json['customer']),
                                 staff_id=current_user.id)
        except Exception as e:
            print(e)
            return jsonify({"status": 500})

    del session[key]

    return redirect('/sales/login')


def comments(book_id):
    data = []
    for c in dao.get_comments(book_id=book_id):
        data.append({
            'id': c.id,
            'content': c.content,
            'created_date': str(c.created_date),
            'user': {
                'name': c.user.username,
                'avatar': c.user.avatar
            }
        })

    return jsonify(data)


def add_comment(book_id):
    content = request.json['content']
    if content == '':
        return jsonify({'status': 501})

    try:
        c = dao.save_comment(book_id=book_id, content=content)
    except:
        return jsonify({'status': 500})

    return jsonify({
        'status': 204,
        'comment': {
            'id': c.id,
            'content': c.content,
            'created_date': str(c.created_date),
            'user': {
                'name': c.user.username,
                'avatar': c.user.avatar
            }
        }
    })


def edit_rules():
    min_quantity = request.form.get('min-quantity')
    max_quantity = request.form.get('max-quantity')
    expired_hours = request.form.get('expired-hours')
    print(min_quantity, max_quantity, expired_hours)

    dao.edit_rule(int(min_quantity), int(max_quantity), int(expired_hours))
    return redirect('/admin/edit_rules/')
