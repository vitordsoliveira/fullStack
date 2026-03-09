from flask import Blueprint, request, jsonify
from seller_model import Seller
from data_base import db
from twilio_service import send_activation_code
import random

seller_bp = Blueprint('seller_bp', __name__)

@seller_bp.route('/api/sellers', methods=['POST'])
def create_seller():
    data = request.get_json()

    if not all(k in data for k in ['nome', 'cnpj', 'email', 'celular', 'senha']):
        return jsonify({'error': 'Dados incompletos'}), 400

    if Seller.query.filter((Seller.email == data['email']) | (Seller.cnpj == data['cnpj'])).first():
        return jsonify({'error': 'E-mail ou CNPJ já cadastrado'}), 409

    activation_code = str(random.randint(1000, 9999))

    new_seller = Seller(
        nome=data['nome'],
        cnpj=data['cnpj'],
        email=data['email'],
        celular=data['celular'],
        status='Inativo',
        activation_code=activation_code
    )
    new_seller.set_password(data['senha'])

    try:
        send_activation_code(new_seller.celular, activation_code)
        
        db.session.add(new_seller)
        db.session.commit()

        return jsonify({'message': 'Cadastro realizado com sucesso! Verifique seu WhatsApp para o código de ativação.'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Falha ao cadastrar ou enviar código: {str(e)}'}), 500

@seller_bp.route('/api/sellers/activate', methods=['POST'])
def activate_seller():
    data = request.get_json()

    if not all(k in data for k in ['celular', 'codigo']):
        return jsonify({'error': 'Celular e código são obrigatórios'}), 400

    seller = Seller.query.filter_by(celular=data['celular']).first()

    if not seller:
        return jsonify({'error': 'Seller não encontrado'}), 404

    if seller.status == 'Ativo':
        return jsonify({'message': 'Esta conta já está ativa'}), 200

    if seller.activation_code == data['codigo']:
        seller.status = 'Ativo'
        seller.activation_code = None 
        db.session.commit()
        return jsonify({'message': 'Conta ativada com sucesso!'}), 200
    else:
        return jsonify({'error': 'Código de ativação inválido'}), 400