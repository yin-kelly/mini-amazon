# app/qa.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from .models.social import ProductQuestion, ProductAnswer, Notification

bp = Blueprint('qa', __name__, url_prefix='/qa')

@bp.route('/product/<int:product_id>/questions')
def product_questions(product_id):
    """View questions for a product"""
    questions = ProductQuestion.get_by_product(product_id)
    
    # Get product info
    product_info = current_app.db.execute('''
        SELECT name FROM Products WHERE product_id = :product_id
    ''', product_id=product_id)
    
    product_name = product_info[0][0] if product_info else f"Product #{product_id}"
    
    return render_template('qa/product_questions.html', 
                         product_id=product_id, 
                         product_name=product_name,
                         questions=questions)

@bp.route('/product/<int:product_id>/ask', methods=['GET', 'POST'])
@login_required
def ask_question(product_id):
    """Ask a question about a product"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        if not title or not content:
            flash('Title and content are required.', 'error')
            return redirect(url_for('qa.ask_question', product_id=product_id))
        
        question_id = ProductQuestion.create(product_id, current_user.id, title, content)
        
        if question_id:
            flash('Your question has been posted!', 'success')
            return redirect(url_for('qa.product_questions', product_id=product_id))
        else:
            flash('Failed to post question.', 'error')
    
    # Get product info
    product_info = current_app.db.execute('''
        SELECT name FROM Products WHERE product_id = :product_id
    ''', product_id=product_id)
    
    product_name = product_info[0][0] if product_info else f"Product #{product_id}"
    
    return render_template('qa/ask_question.html', 
                         product_id=product_id, 
                         product_name=product_name)

@bp.route('/question/<int:question_id>/answer', methods=['POST'])
@login_required
def answer_question(question_id):
    """Answer a question"""
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Answer content is required.', 'error')
        return redirect(request.referrer or url_for('index.index'))
    
    # Get question info
    question_info = current_app.db.execute('''
        SELECT q.product_id, q.asker_id, q.title
        FROM ProductQuestions q
        WHERE q.question_id = :question_id
    ''', question_id=question_id)
    
    if not question_info:
        flash('Question not found.', 'error')
        return redirect(url_for('index.index'))
    
    question_data = question_info[0]
    product_id = question_data[0]
    asker_id = question_data[1]
    question_title = question_data[2]
    
    answer_id = ProductAnswer.create(question_id, current_user.id, content)
    
    if answer_id:
        # Create notification for question asker
        Notification.create(asker_id, 'answer', {
            'question_id': question_id,
            'question_title': question_title,
            'product_id': product_id,
            'answerer_name': f"{current_user.firstname} {current_user.lastname}"
        })
        
        flash('Your answer has been posted!', 'success')
    else:
        flash('Failed to post answer.', 'error')
    
    return redirect(url_for('qa.product_questions', product_id=product_id))
