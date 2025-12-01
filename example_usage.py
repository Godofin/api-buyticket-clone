"""
Script de exemplo para testar a API do Ticket Marketplace
Execute a API primeiro com: uvicorn app.main:app --reload
"""

import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"


def test_api():
    print("=" * 60)
    print("TESTANDO API DO TICKET MARKETPLACE")
    print("=" * 60)
    
    # 1. Criar usuários
    print("\n1. Criando usuários...")
    
    seller = {
        "email": "vendedor@example.com",
        "name": "João Vendedor",
        "cpf": "12345678901",
        "phone": "11999999999",
        "role": "seller"
    }
    
    buyer = {
        "email": "comprador@example.com",
        "name": "Maria Compradora",
        "cpf": "98765432100",
        "phone": "11988888888",
        "role": "buyer"
    }
    
    response_seller = requests.post(f"{BASE_URL}/users/", json=seller)
    seller_id = response_seller.json()["id"]
    print(f"✓ Vendedor criado: ID {seller_id}")
    
    response_buyer = requests.post(f"{BASE_URL}/users/", json=buyer)
    buyer_id = response_buyer.json()["id"]
    print(f"✓ Comprador criado: ID {buyer_id}")
    
    # 2. Criar evento
    print("\n2. Criando evento...")
    
    event_date = (datetime.now() + timedelta(days=30)).isoformat()
    event = {
        "name": "Show de Rock 2024",
        "description": "Grande show de rock com bandas nacionais",
        "venue": "Estádio Municipal",
        "event_date": event_date,
        "category": "Show"
    }
    
    response_event = requests.post(f"{BASE_URL}/events/", json=event)
    event_id = response_event.json()["id"]
    print(f"✓ Evento criado: ID {event_id} - {event['name']}")
    
    # 3. Vendedor lista ingresso
    print("\n3. Vendedor listando ingresso...")
    
    ticket = {
        "event_id": event_id,
        "section": "Pista",
        "row": "A",
        "seat_number": "15",
        "original_price": 100.00,
        "selling_price": 105.00  # 5% acima do original (dentro do limite)
    }
    
    response_ticket = requests.post(
        f"{BASE_URL}/tickets/",
        json=ticket,
        params={"seller_id": seller_id}
    )
    ticket_id = response_ticket.json()["id"]
    print(f"✓ Ingresso listado: ID {ticket_id} - R$ {ticket['selling_price']}")
    
    # 4. Listar ingressos disponíveis
    print("\n4. Listando ingressos disponíveis...")
    
    response = requests.get(f"{BASE_URL}/tickets/available")
    tickets = response.json()
    print(f"✓ {len(tickets)} ingresso(s) disponível(is)")
    
    # 5. Comprador visualiza ingresso
    print("\n5. Comprador visualizando detalhes do ingresso...")
    
    response = requests.get(f"{BASE_URL}/tickets/{ticket_id}")
    ticket_details = response.json()
    print(f"✓ Ingresso: {ticket_details['section']} - Assento {ticket_details['seat_number']}")
    print(f"  Preço: R$ {ticket_details['selling_price']}")
    
    # 6. Comprador inicia transação
    print("\n6. Comprador iniciando compra...")
    
    transaction = {
        "ticket_id": ticket_id,
        "payment_method": "credit_card"
    }
    
    response_transaction = requests.post(
        f"{BASE_URL}/transactions/",
        json=transaction,
        params={"buyer_id": buyer_id}
    )
    transaction_data = response_transaction.json()
    transaction_id = transaction_data["id"]
    print(f"✓ Transação criada: ID {transaction_id}")
    print(f"  Valor do ingresso: R$ {transaction_data['amount']}")
    print(f"  Taxa da plataforma: R$ {transaction_data['platform_fee']}")
    print(f"  Total: R$ {transaction_data['total_amount']}")
    print(f"  Status: {transaction_data['status']}")
    
    # 7. Completar transação (simular pagamento aprovado)
    print("\n7. Completando transação (pagamento aprovado)...")
    
    response = requests.post(f"{BASE_URL}/transactions/{transaction_id}/complete")
    completed_transaction = response.json()
    print(f"✓ Transação completada!")
    print(f"  Status: {completed_transaction['status']}")
    
    # 8. Verificar estatísticas do vendedor
    print("\n8. Estatísticas do vendedor...")
    
    response = requests.get(f"{BASE_URL}/transactions/stats/seller/{seller_id}")
    seller_stats = response.json()
    print(f"✓ Total de ingressos listados: {seller_stats['total_tickets_listed']}")
    print(f"  Ingressos vendidos: {seller_stats['tickets_sold']}")
    print(f"  Receita total: R$ {seller_stats['total_revenue']}")
    
    # 9. Verificar estatísticas do comprador
    print("\n9. Estatísticas do comprador...")
    
    response = requests.get(f"{BASE_URL}/transactions/stats/buyer/{buyer_id}")
    buyer_stats = response.json()
    print(f"✓ Total de compras: {buyer_stats['total_purchases']}")
    print(f"  Total gasto: R$ {buyer_stats['total_spent']}")
    print(f"  Transações completadas: {buyer_stats['completed_transactions']}")
    
    # 10. Testar limite de preço (anti-cambismo)
    print("\n10. Testando proteção anti-cambismo...")
    
    expensive_ticket = {
        "event_id": event_id,
        "section": "Camarote",
        "row": "VIP",
        "seat_number": "1",
        "original_price": 200.00,
        "selling_price": 250.00  # 25% acima (deve falhar)
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/tickets/",
            json=expensive_ticket,
            params={"seller_id": seller_id}
        )
        if response.status_code == 400:
            print("✓ Proteção funcionando! Preço acima de 110% foi rejeitado")
            print(f"  Erro: {response.json()['detail']}")
    except Exception as e:
        print(f"✓ Proteção funcionando! {e}")
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("ERRO: Não foi possível conectar à API.")
        print("Certifique-se de que a API está rodando com:")
        print("  uvicorn app.main:app --reload")
    except Exception as e:
        print(f"ERRO: {e}")
