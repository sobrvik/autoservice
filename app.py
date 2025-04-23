from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Service, Request, AdminUser, Feedback
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Створити БД при першому запуску
@app.before_request
def create_tables():
    db.create_all()
    # Створити адміна за замовчуванням, якщо не існує
    if not AdminUser.query.filter_by(username='admin').first():
        admin = AdminUser(username='admin', password=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()

# Головна сторінка
@app.route('/')
def index():
    services = Service.query.all()
    return render_template('index.html', services=services)

# Записатись
@app.route('/sign')
def sign():
    services = Service.query.all()
    return render_template('sign.html', services=services)

# Надіслати заявку
@app.route('/submit-request', methods=['POST'])
def submit_request():
    name = request.form['name']
    phone = request.form['phone']
    car_brand = request.form['car_brand']
    service_id = request.form['service']
    comment = request.form.get('comment')

    new_request = Request(name=name, phone=phone, car_brand=car_brand, service_id=service_id, comment=comment)
    db.session.add(new_request)
    db.session.commit()

    flash("Заявка успішно надіслана!")
    return redirect(url_for('index'))

# Видалити заявку
@app.route('/admin/delete-request/<int:request_id>', methods=['GET'])
def delete_request(request_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    request_to_delete = Request.query.get_or_404(request_id)
    db.session.delete(request_to_delete)
    db.session.commit()
    
    flash("Заявку успішно видалено!")
    return redirect(url_for('admin_dashboard'))

# Надіслати фідбек
@app.route('/feedback', methods=['POST'])
def feedback():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    new_feedback = Feedback(name=name, email=email, message=message)
    db.session.add(new_feedback)
    db.session.commit()

    flash("Дякуємо! Ваше повідомлення збережено.")
    return redirect(url_for('index'))

# Видалити фідбек
@app.route('/admin/delete-feedback/<int:feedback_id>')
def delete_feedback(feedback_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    feedback = Feedback.query.get_or_404(feedback_id)
    db.session.delete(feedback)
    db.session.commit()
    flash("Відгук успішно видалено!")
    return redirect(url_for('admin_dashboard'))

# Вхід в адмінку
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user = AdminUser.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['admin'] = user.username
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Невірний логін або пароль")
    return render_template('admin_login.html')

# Адмін-панель
@app.route('/admin')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    requests = Request.query.order_by(Request.created_at.desc()).all()
    services = Service.query.all()
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()

    return render_template(
        'admin.html',
        requests=requests,
        services=services,
        feedbacks=feedbacks
    )
    
# Додати послугу
@app.route('/admin/add-service', methods=['POST'])
def add_service():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    name = request.form['service_name']
    if name:
        db.session.add(Service(name=name))
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

# Видалити послугу
@app.route('/admin/delete-service/<int:service_id>', methods=['GET'])
def delete_service(service_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    service_to_delete = Service.query.get_or_404(service_id)
    db.session.delete(service_to_delete)
    db.session.commit()
    
    flash("Послугу успішно видалено!")
    return redirect(url_for('admin_dashboard'))

# Вийти з адмінки
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)