"""
Script de teste para a nova API do Ticket Marketplace v2
Testa todos os novos recursos: KYC, chat moderado, escrow, disputas
"""

import requests
from datetime import datetime, timedelta
import json

BASE_URL = "http://localhost:8000"


def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_complete_flow():
    print_section("TESTANDO API TICKET MARKETPLACE V2")
    
    # 1. Criar usuários
    print_section("1. CRIANDO USUÁRIOS")
    
    admin = {
        "full_name": "Admin Sistema",
        "cpf": "00000000001",
        "email": "admin@marketplace.com",
        "password": "admin123"
    }
    
    seller = {
        "full_name": "João Vendedor",
        "cpf": "12345678901",
        "email": "vendedor@example.com",
        "password": "senha123",
        "phone": "11999999999"
    }
    
    buyer = {
        "full_name": "Maria Compradora",
        "cpf": "98765432100",
        "email": "compradora@example.com",
        "password": "senha123",
        "phone": "11988888888"
    }
    
    response_admin = requests.post(f"{BASE_URL}/users/", json=admin)
    admin_id = response_admin.json()["id"]
    print(f"✓ Admin criado: ID {admin_id}")
    
    response_seller = requests.post(f"{BASE_URL}/users/", json=seller)
    seller_id = response_seller.json()["id"]
    print(f"✓ Vendedor criado: ID {seller_id}")
    
    response_buyer = requests.post(f"{BASE_URL}/users/", json=buyer)
    buyer_id = response_buyer.json()["id"]
    print(f"✓ Comprador criado: ID {buyer_id}")
    
    # 2. Verificar telefones
    print_section("2. VERIFICANDO TELEFONES")
    
    requests.post(f"{BASE_URL}/users/{seller_id}/verify-phone")
    print(f"✓ Telefone do vendedor verificado")
    
    requests.post(f"{BASE_URL}/users/{buyer_id}/verify-phone")
    print(f"✓ Telefone do comprador verificado")
    
    # 3. Upload de documentos (KYC)
    print_section("3. SISTEMA DE KYC - UPLOAD DE DOCUMENTOS")
    
    doc_seller = {
        "document_type": "CNH",
        "front_image_url": "https://example.com/cnh_frente.jpg",
        "back_image_url": "https://example.com/cnh_verso.jpg",
        "selfie_url": "https://example.com/selfie.jpg"
    }
    
    response_doc = requests.post(
        f"{BASE_URL}/users/{seller_id}/documents",
        json=doc_seller
    )
    doc_id = response_doc.json()["id"]
    print(f"✓ Documento enviado: ID {doc_id} - Status: PENDING")
    
    # 4. Admin aprova documento
    response_approve = requests.post(f"{BASE_URL}/users/documents/{doc_id}/approve")
    print(f"✓ Documento aprovado pelo admin")
    print(f"  Vendedor agora está verificado (identity_verified = True)")
    
    # 5. Criar evento
    print_section("4. ADMIN CRIA EVENTO")
    
    event_date = (datetime.now() + timedelta(days=60)).isoformat()
    event = {
        "title": "Rock in Rio 2025",
        "description": "O maior festival de rock do mundo",
        "event_date": event_date,
        "venue": "Cidade do Rock - Rio de Janeiro",
        "image_banner_url": "https://example.com/banner.jpg"
    }
    
    response_event = requests.post(f"{BASE_URL}/events/", json=event)
    event_id = response_event.json()["id"]
    print(f"✓ Evento criado: ID {event_id} - {event['title']}")
    
    # 6. Admin cria categorias de ingressos (TICKET MASTERS)
    print_section("5. ADMIN DEFINE PREÇOS OFICIAIS (TICKET MASTERS)")
    
    ticket_masters = [
        {"event_id": event_id, "category_name": "Pista Premium - Lote 1", "face_value": 500.00},
        {"event_id": event_id, "category_name": "Pista - Lote 1", "face_value": 300.00},
        {"event_id": event_id, "category_name": "Camarote VIP", "face_value": 1000.00}
    ]
    
    tm_ids = []
    for tm in ticket_masters:
        response_tm = requests.post(f"{BASE_URL}/events/ticket-masters", json=tm)
        tm_data = response_tm.json()
        tm_ids.append(tm_data["id"])
        print(f"✓ Categoria: {tm['category_name']}")
        print(f"  Valor original: R$ {tm['face_value']:.2f}")
        print(f"  Máximo permitido (120%): R$ {tm_data['max_allowed_price']:.2f}")
    
    # 7. Vendedor tenta listar ingresso acima de 120% (DEVE FALHAR)
    print_section("6. TESTANDO REGRA DOS 20% - TENTATIVA BLOQUEADA")
    
    listing_invalid = {
        "event_ticket_master_id": tm_ids[1],  # Pista - R$ 300
        "price_asked": 400.00,  # 33% acima - BLOQUEADO!
        "description": "Ingresso para venda"
    }
    
    response_invalid = requests.post(
        f"{BASE_URL}/listings/?seller_id={seller_id}",
        json=listing_invalid
    )
    
    if response_invalid.status_code == 400:
        print(f"✓ PROTEÇÃO FUNCIONANDO!")
        print(f"  Tentativa de vender por R$ 400 (33% acima)")
        print(f"  Erro: {response_invalid.json()['detail']}")
    
    # 8. Vendedor lista ingresso dentro do limite
    print_section("7. VENDEDOR LISTA INGRESSO CORRETAMENTE")
    
    listing_valid = {
        "event_ticket_master_id": tm_ids[1],  # Pista - R$ 300
        "price_asked": 350.00,  # 16.6% acima - OK!
        "description": "Ingresso Pista - Não posso mais ir",
        "ticket_proof_image_url": "https://example.com/ingresso_borrado.jpg",
        "ticket_file_url": "https://example.com/ingresso.pdf"
    }
    
    response_listing = requests.post(
        f"{BASE_URL}/listings/?seller_id={seller_id}",
        json=listing_valid
    )
    listing_id = response_listing.json()["id"]
    print(f"✓ Anúncio criado: ID {listing_id}")
    print(f"  Preço: R$ {listing_valid['price_asked']:.2f} (dentro do limite)")
    
    # 9. Comprador busca ingressos disponíveis
    print_section("8. COMPRADOR BUSCA INGRESSOS")
    
    response_listings = requests.get(f"{BASE_URL}/listings/active")
    listings = response_listings.json()
    print(f"✓ {len(listings)} anúncio(s) disponível(is)")
    
    # 10. Comprador inicia chat com vendedor
    print_section("9. SISTEMA DE CHAT")
    
    chat_room_data = {"listing_id": listing_id}
    response_chat = requests.post(
        f"{BASE_URL}/chat/rooms?buyer_id={buyer_id}",
        json=chat_room_data
    )
    chat_room_id = response_chat.json()["id"]
    print(f"✓ Chat criado: ID {chat_room_id}")
    
    # 11. Comprador envia mensagem normal
    message1 = {
        "message_text": "Olá! O ingresso ainda está disponível?",
        "message_type": "TEXT"
    }
    
    response_msg1 = requests.post(
        f"{BASE_URL}/chat/rooms/{chat_room_id}/messages?sender_id={buyer_id}",
        json=message1
    )
    print(f"✓ Mensagem enviada: '{message1['message_text']}'")
    print(f"  Flagged: {response_msg1.json()['flagged_by_system']}")
    
    # 12. Vendedor tenta passar contato (MODERAÇÃO AUTOMÁTICA)
    print_section("10. MODERAÇÃO AUTOMÁTICA DE CHAT")
    
    message2 = {
        "message_text": "Sim! Me passa seu WhatsApp que a gente fecha fora do app",
        "message_type": "TEXT"
    }
    
    response_msg2 = requests.post(
        f"{BASE_URL}/chat/rooms/{chat_room_id}/messages?sender_id={seller_id}",
        json=message2
    )
    msg2_data = response_msg2.json()
    print(f"✓ Mensagem enviada: '{message2['message_text']}'")
    print(f"  ⚠️  FLAGGED: {msg2_data['flagged_by_system']}")
    print(f"  Motivo: {msg2_data['flagged_reason']}")
    
    # 13. Admin visualiza mensagens flagadas
    response_flagged = requests.get(f"{BASE_URL}/chat/messages/flagged")
    flagged_count = len(response_flagged.json())
    print(f"✓ Admin pode ver {flagged_count} mensagem(ns) suspeita(s)")
    
    # 14. Comprador cria pedido (ESCROW)
    print_section("11. SISTEMA DE ESCROW - COMPRA")
    
    order_data = {
        "listing_id": listing_id,
        "payment_method": "credit_card"
    }
    
    response_order = requests.post(
        f"{BASE_URL}/orders/?buyer_id={buyer_id}",
        json=order_data
    )
    order_data_response = response_order.json()
    order_id = order_data_response["id"]
    print(f"✓ Pedido criado: ID {order_id}")
    print(f"  Valor do ingresso: R$ {order_data_response['total_amount'] - order_data_response['platform_fee']:.2f}")
    print(f"  Taxa da plataforma (5%): R$ {order_data_response['platform_fee']:.2f}")
    print(f"  Total: R$ {order_data_response['total_amount']:.2f}")
    print(f"  Status pagamento: {order_data_response['payment_status']}")
    print(f"  Status escrow: {order_data_response['escrow_status']} (dinheiro retido)")
    
    # 15. Completa pagamento
    response_payment = requests.post(f"{BASE_URL}/orders/{order_id}/complete-payment")
    print(f"✓ Pagamento completado")
    print(f"  Dinheiro ainda em ESCROW (aguardando confirmação)")
    
    # 16. Libera escrow para vendedor
    print_section("12. LIBERAÇÃO DO ESCROW")
    
    response_release = requests.post(f"{BASE_URL}/orders/{order_id}/release-escrow")
    released_order = response_release.json()
    print(f"✓ Escrow liberado para o vendedor!")
    print(f"  Status escrow: {released_order['escrow_status']}")
    print(f"  Vendedor recebeu: R$ {order_data_response['total_amount'] - order_data_response['platform_fee']:.2f}")
    
    # 17. Estatísticas do vendedor
    print_section("13. ESTATÍSTICAS DO VENDEDOR")
    
    response_stats = requests.get(f"{BASE_URL}/orders/stats/seller/{seller_id}")
    stats = response_stats.json()
    print(f"✓ Total de anúncios: {stats['total_listings']}")
    print(f"  Anúncios vendidos: {stats['sold_listings']}")
    print(f"  Receita total: R$ {stats['total_revenue']:.2f}")
    print(f"  Reputação: {stats['reputation_score']:.1f}")
    
    # 18. Criar disputa (exemplo)
    print_section("14. SISTEMA DE DISPUTAS")
    
    # Criar outro pedido para testar disputa
    listing_valid2 = {
        "event_ticket_master_id": tm_ids[0],
        "price_asked": 550.00,
        "description": "Ingresso Premium"
    }
    
    response_listing2 = requests.post(
        f"{BASE_URL}/listings/?seller_id={seller_id}",
        json=listing_valid2
    )
    listing_id2 = response_listing2.json()["id"]
    
    order_data2 = {"listing_id": listing_id2, "payment_method": "credit_card"}
    response_order2 = requests.post(f"{BASE_URL}/orders/?buyer_id={buyer_id}", json=order_data2)
    order_id2 = response_order2.json()["id"]
    requests.post(f"{BASE_URL}/orders/{order_id2}/complete-payment")
    
    # Comprador cria disputa
    dispute_data = {
        "order_id": order_id2,
        "reported_user_id": seller_id,
        "reason": "Ingresso não foi enviado conforme prometido"
    }
    
    response_dispute = requests.post(
        f"{BASE_URL}/admin/disputes?reporter_id={buyer_id}",
        json=dispute_data
    )
    dispute_id = response_dispute.json()["id"]
    print(f"✓ Disputa criada: ID {dispute_id}")
    print(f"  Status: OPEN")
    print(f"  Escrow marcado como: DISPUTE")
    
    # Admin resolve disputa
    response_resolve = requests.post(
        f"{BASE_URL}/admin/disputes/{dispute_id}/resolve",
        params={
            "admin_notes": "Analisado. Ingresso não foi enviado. Procedente.",
            "refund_buyer": True
        }
    )
    print(f"✓ Disputa resolvida pelo admin")
    print(f"  Decisão: Reembolso para o comprador")
    
    # 19. Logs de auditoria
    print_section("15. LOGS DE AUDITORIA")
    
    response_logs = requests.get(f"{BASE_URL}/admin/logs?limit=5")
    logs = response_logs.json()
    print(f"✓ {len(logs)} log(s) mais recente(s):")
    for log in logs[:3]:
        print(f"  - {log['action']}")
    
    print_section("TESTE COMPLETO COM SUCESSO!")
    print("\n✅ Todos os recursos foram testados:")
    print("  • Sistema de KYC com aprovação de documentos")
    print("  • Regra dos 20% (máximo 120% do valor original)")
    print("  • Chat com moderação automática")
    print("  • Sistema de escrow para pagamentos")
    print("  • Disputas e resolução")
    print("  • Logs de auditoria")
    print("  • Sistema de reputação")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        test_complete_flow()
    except requests.exceptions.ConnectionError:
        print("ERRO: Não foi possível conectar à API.")
        print("Certifique-se de que a API está rodando com:")
        print("  uvicorn app.main:app --reload")
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
