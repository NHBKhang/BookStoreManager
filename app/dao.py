import hashlib
import os
import json, numpy
from app.models import *
from app import db, app
from sqlalchemy import desc, func, extract
from flask_login import current_user
from datetime import datetime, timedelta


def get_categories():
    return Category.query.all()


def get_books(kw=None, cate_id=None, page=None, desc=True):
    books = Book.query
    if kw:
        books = books.filter(Book.name.contains(kw))
    if cate_id:
        books = books.filter(Book.categories.any(Book_Category.category_id == cate_id))
    if desc:
        books = books.order_by(Book.id.desc())
    if page:
        page = int(page)
        page_size = app.config['PAGE_SIZE']
        start = (page - 1) * page_size
        books = books.slice(start, start + page_size)

    return books.all()


def get_orders(customer_id):
    return Order.query.filter_by(customer_id=customer_id).all()


def get_order_details(order_id):
    return OrderDetails.query.filter_by(order_id=order_id).all()


def get_authors():
    return Author.query.all()


def get_book_inventory(book_id):
    return Book_Inventory.query.filter_by(book_id=book_id).first()


def get_inventories():
    return Inventory.query.all()


def get_comments(book_id):
    return Comment.query.filter(Comment.book_id.__eq__(book_id)).order_by(-Comment.id).all()


def count_books():  # Count number of product in database
    return Book.query.count()


def get_customers():
    return User.query.filter(User.id.__eq__(Customer.id))


def get_book_by_id(book_id):
    return Book.query.get(book_id)


def get_inventory_by_id(inventory_id):
    return Inventory.query.get(inventory_id)


def get_authors_by_book_id(book_id):
    book_author = Book_Author.query.filter(Book_Author.book_id == book_id).all()
    return [Author.query.get(a.author_id) for a in book_author]


def get_categories_by_book_id(book_id):
    book_category = Book_Category.query.filter(Book_Category.book_id == book_id).all()
    return [Category.query.get(a.category_id) for a in book_category]


def get_user_by_id(user_id):
    return User.query.get(user_id)


def get_admin_by_id(admin_id):
    return Admin.query.get(admin_id)


def get_account_by_id(account_id):
    return Account.query.get(account_id)


def get_order_by_id(order_id):
    return Order.query.get(order_id)


def get_vnpay_history_by_id(history_id):
    return VNPAY_History.query.get(history_id)


def get_carousel_items():
    with open(os.path.join(app.root_path, "static/data/carousel.json"), encoding="utf-8") as c:
        return json.load(c)


def get_rule():
    with open(os.path.join(app.root_path, "static/data/rules.json"), encoding="utf-8") as r:
        return json.load(r)


def edit_rule(min_quantity=None, max_quantity=None, expired_hours=None):
    rule = {
        "min_quantity": 150,
        "max_quantity": 300,
        "expired_hours": 48
    }
    if min_quantity:
        rule["min_quantity"] = min_quantity
    if max_quantity:
        rule["max_quantity"] = max_quantity
    if expired_hours:
        rule["expired_hours"] = expired_hours
    with open(os.path.join(app.root_path, "static/data/rules.json"), 'w', encoding="utf-8") as r:
        r.write(json.dumps(rule, indent=2))


def auth_account(username, password, type='admin'):
    import hashlib

    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

    if type == 'admin':
        return Admin.query.filter(Admin.username.__eq__(username.strip()),
                                  Admin.password.__eq__(password)).first()
    else:
        return User.query.filter(User.username.__eq__(username.strip()),
                                 User.password.__eq__(password)).first()


def update_order_status(order_id, status=None):
    o = get_order_by_id(order_id)
    if status is not None:
        if datetime.now() - o.created_date > timedelta(hours=get_rule()['expired_hours']):
            o.status = OrderStatus.REJECTED
    else:
        o.status = status
    db.session.add(o)
    db.session.commit()


def update_book(book_id, name, price, description, image, published_date):
    Book.query.filter_by(id=book_id).update(
        dict(name=name, price=price, description=description, image=image, published_date=published_date))

    Book_Category.query.filter_by(book_id=book_id).delete()
    Book_Author.query.filter_by(book_id=book_id).delete()
    Book_Inventory.query.filter_by(book_id=book_id).delete()
    db.session.commit()


def update_order(order_id, transaction_id, status=OrderStatus.APPROVED, is_paid=True):
    o = get_order_by_id(order_id)
    o.transaction_id = transaction_id
    o.status = status
    o.is_paid = is_paid
    db.session.add(o)
    db.session.commit()


def save_receipt(cart, customer_id, staff_id):
    if cart:
        r = Receipt(customer_id=customer_id, staff_id=staff_id)
        db.session.add(r)
        db.session.commit()

        for c in cart.values():
            d = ReceiptDetails(quantity=c['quantity'], price=c['price'], receipt_id=r.id, book_id=c['id'])
            db.session.add(d)
            db.session.commit()

        return r


def save_order(cart, is_paid=False):
    if cart:
        o = add_order(customer_id=current_user.id, is_paid=is_paid)
        if is_paid:
            r = add_receipt(customer_id=current_user.id, staff_id=3)

        for c in cart.values():
            add_order_details(order_id=o.id, quantity=c['quantity'], price=c['price'], book_id=c['id'])
            if is_paid:
                add_receipt_details(receipt_id=r.id, quantity=c['quantity'], price=c['price'], book_id=c['id'])

        return o


def save_comment(content, book_id):
    c = Comment(content=content, book_id=book_id, user_id=int(current_user.id))
    db.session.add(c)
    db.session.commit()
    return c


def save_vnpay_history(transaction_id, bank_code, description):
    h = VNPAY_History(transaction_id=transaction_id, bank_code=bank_code, description=description)
    db.session.add(h)
    db.session.commit()
    return h


def add_admin(username, password, name, email, status=AccountStatus.ACTIVE, avatar='avatar_male.png'):
    admin = Admin(username=username, password=hashlib.md5(password.strip().encode('utf-8')).hexdigest(), status=status,
                  avatar=avatar, name=name, email=email)
    db.session.add(admin)
    db.session.commit()


def add_customer(username, password, name, first_name, last_name, birthday, email, phone, address,
                 gender=GenderType.MALE,
                 status=AccountStatus.ACTIVE, avatar='avatar_male.png', customer_type=CustomerType.GUEST):
    customer = Customer(username=username, password=hashlib.md5(password.strip().encode('utf-8')).hexdigest(),
                        status=status, avatar=avatar, first_name=first_name, last_name=last_name, phone=phone,
                        birthday=datetime.strptime(birthday, '%Y-%m-%d'), email=email, gender=gender,
                        address=address, customer_type=customer_type, name=name if name else username)
    db.session.add(customer)
    db.session.commit()


def add_book(name, price, img, description, date):
    b = Book(name=name, price=price,
             image=img,
             description=description,
             published_date=datetime.strptime(date, '%Y-%m-%d'))
    db.session.add_all([b])
    db.session.commit()
    return b


def add_book_inventory(book_id, inventory_id=1, quantity=150):
    bi = Book_Inventory(book_id=book_id, inventory_id=inventory_id, quantity=quantity)
    db.session.add(bi)
    db.session.commit()


def add_book_category(book_id, category_id):
    ba = Book_Category(book_id=book_id, category_id=category_id)
    db.session.add(ba)
    db.session.commit()


def add_book_author(book_id, author_id):
    ba = Book_Author(book_id=book_id, author_id=author_id)
    db.session.add(ba)
    db.session.commit()


def add_order(customer_id, created_date=datetime.now(), updated_date=datetime.now(), status=OrderStatus.PENDING,
              is_paid=False):
    o = Order(customer_id=customer_id, created_date=created_date, updated_date=updated_date, status=status,
              is_paid=is_paid)
    db.session.add(o)
    db.session.commit()
    return o


def add_order_details(order_id, book_id, price=None, quantity=1):
    if price is None:
        price = dao.get_book_by_id(book_id).price
    o = OrderDetails(order_id=order_id, book_id=book_id, price=price, quantity=quantity)
    db.session.add(o)
    db.session.commit()


def add_receipt(customer_id, staff_id, created_date=datetime.now()):
    r = Receipt(customer_id=customer_id, staff_id=staff_id, created_date=created_date)
    db.session.add(r)
    db.session.commit()
    return r


def add_receipt_details(receipt_id, book_id, price=None, quantity=1):
    if price is None:
        price = dao.get_book_by_id(book_id).price
    d = ReceiptDetails(receipt_id=receipt_id, quantity=quantity, price=price, book_id=book_id)
    db.session.add(d)
    db.session.commit()


def books_revenue_stats(kw=None, from_date=None, to_date=None):
    query = db.session.query(Book.id, Book.name, func.sum(ReceiptDetails.price * ReceiptDetails.quantity)) \
        .join(ReceiptDetails, ReceiptDetails.book_id.__eq__(Book.id)) \
        .join(Receipt, ReceiptDetails.receipt_id.__eq__(Receipt.id))

    if kw:
        query = query.filter(Book.name.contains(kw))

    if from_date:
        query = query.filter(Receipt.created_date.__ge__(from_date))

    if to_date:
        query = query.filter(Receipt.created_date.__le__(to_date))

    return query.group_by(Book.id).order_by(-Book.id).all()


def categories_stats():
    return Category.query.join(Book, Book.categories.any(Book_Category.category_id.__eq__(Category.id)), isouter=True) \
        .add_columns(func.count(Book.id)).group_by(Category.id).all()


def categories_revenue_stats(month, year):
    return (Category.query.filter((extract('month', Receipt.created_date).__eq__(month))
                                  .__and__(extract('year', Receipt.created_date).__eq__(year)))
            .add_column(func.sum(ReceiptDetails.price * ReceiptDetails.quantity))
            .add_column(func.sum(ReceiptDetails.quantity))
            .join(Book_Category, Book_Category.category_id.__eq__(Category.id))
            .join(Book, Book_Category.book_id.__eq__(Book.id))
            .join(ReceiptDetails, ReceiptDetails.book_id.__eq__(Book.id))
            .join(Receipt, ReceiptDetails.receipt_id.__eq__(Receipt.id))
            .group_by(Category.id).order_by(Category.id).all())


def categories_total_revenue(month, year):
    return numpy.sum(r.price * r.quantity for r in ReceiptDetails.query
                     .filter((extract('month', Receipt.created_date) == month)
                             .__and__(extract('year', Receipt.created_date) == year)).all())


def books_frequency_stats(month, year):
    return (Book.query.filter((extract('month', Receipt.created_date).__eq__(month))
                              .__and__(extract('year', Receipt.created_date).__eq__(year)))
            .add_columns(func.sum(ReceiptDetails.quantity))
            .join(ReceiptDetails, ReceiptDetails.book_id.__eq__(Book.id))
            .join(Receipt, ReceiptDetails.receipt_id.__eq__(Receipt.id))
            .group_by(Book.id).order_by(Book.id).all())


def delete_book_by_id(book_id):
    Book_Inventory.query.filter_by(book_id=book_id).delete()
    Book_Author.query.filter_by(book_id=book_id).delete()
    Book_Category.query.filter_by(book_id=book_id).delete()
    Book.query.filter_by(id=book_id).delete()
    db.session.commit()
