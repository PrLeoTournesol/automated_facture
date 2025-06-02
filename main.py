import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
import json
from datetime import date
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import smtplib
from email.message import EmailMessage


now = date.today()

st.set_page_config(
    page_title="Envoi automatique de factures",
    page_icon="📝",
    layout="wide"
)

if "submitted" not in st.session_state:
    st.session_state["submitted"] = False
if "modified" not in st.session_state:
    st.session_state["modified"] = False
if "sent" not in st.session_state:
    st.session_state["sent"] = False
if "created" not in st.session_state:
    st.session_state["created"] = False
if "removed" not in st.session_state:
    st.session_state["removed"] = False


st.title("Outil d'envoi automatique de facture")
st.markdown("---")

def create_pdf(is_paid, facture_number, emission_date, name, address, email, is_association, amount, tva, now):

    year = now.year
    month = now.month

    doc = SimpleDocTemplate(f"factures/facture_{year}_{month}.pdf")
    styles = getSampleStyleSheet()
    story = []

    # Custom centered style
    centered = ParagraphStyle(name="Centered", parent=styles["Normal"], alignment=TA_CENTER, fontSize=12)
    title_style = ParagraphStyle(name="Title", parent=centered, fontSize=18)
    indented_style = ParagraphStyle('indented', parent=styles['Normal'], leftIndent=20)
    double_indented_style = ParagraphStyle('double_indented', parent=styles['Normal'], leftIndent=40)

    # Header
    story.append(Paragraph(f"<b>FACTURE {is_paid.upper()}</b><br/><br/><b>O2C</b>", title_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<br/><i>SIRET : 935 215 814 </i>", centered))
    story.append(Spacer(1, 3))
    story.append(Paragraph("15 rue de l'Estrapade, 75005 Paris", centered))
    story.append(Spacer(1, 3))
    story.append(Paragraph("Email : contact@o2c.io", centered))
    story.append(Spacer(1, 3))
    story.append(Paragraph("Site Web : <a href='https://o2c.io'>O2C.io</a>", centered))
    story.append(Spacer(1, 100))

    # Invoice info
    story.append(Paragraph(f"<b>Facture N° :</b> {year}{str(facture_number).zfill(3)}<br/><b>Date d'émission :</b> {emission_date}", styles["Normal"]))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%"))
    story.append(Spacer(1, 4))

    # Client info
    if is_association == "Association":
        story.append(Paragraph(f"<b>Coordonnées du client</b><br/>Nom de l'association : {name}<br/>Adresse : {address}<br/>Email : {email}", styles["Normal"]))
    else :
        story.append(Paragraph(f"<b>Coordonnées du client</b><br/>Nom de l'entreprise : {name}<br/>Adresse : {address}<br/>Email : {email}", styles["Normal"]))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%"))
    story.append(Spacer(1, 4))

    # Prestation details
    story.append(Paragraph("<b>Détails de la prestation</b>", styles["Normal"]))

    # Table data
    data = [
        ["", Paragraph("<b>Description</b>", styles["Normal"]), Paragraph("<b>Quantité</b>", styles["Normal"]), Paragraph("<b>Prix unitaire (HT)</b>", styles["Normal"]), Paragraph("<b>Montant (HT)</b>", styles["Normal"])],
        ["", Paragraph("Élaboration d'une double comptabilité<br/> économique et environnementale", styles["Normal"]), "1", f"{amount} €", f"{amount} €"]
    ]

    table = Table(data, colWidths=[8.5, 200, 60, 100, 100])
    table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))

    story.append(table)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%"))
    story.append(Spacer(1, 4))

    # Totals
    if tva == 0:
        story.append(Paragraph(f"<b>Total HT : {amount} €</b><br/><b>TVA</b> non applicable - article 293 B du CGI: CGI : Code général des impôts<br/><b>Total TTC : {amount} €</b>", styles["Normal"]))
    else:
        story.append(Paragraph(f"<b>Total HT : {amount} €</b><br/><b>TVA : </b> {tva} % <br/><b>Total TTC : {amount*(1+tva/100):.02f} €</b>", styles["Normal"]))
    story.append(Spacer(1, 4)) 
    story.append(HRFlowable(width="100%"))
    story.append(Spacer(1, 4))

    # Payment conditions (simulated list)
    story.append(Paragraph("<b>Condition de règlement :</b>", styles["Normal"]))
    story.append(Paragraph("• Paiement à effectuer sous 7 jours", indented_style))
    story.append(Paragraph("• Par virement bancaire à :", indented_style))
    story.append(Paragraph("<b>Titulaire du compte :</b> O2C<br/>\t<b>IBAN :</b> FR76 1820 6001 4165 1145 6046 908<br/>\t<b>BIC :</b> AGRIFRPP882", double_indented_style))
    story.append(Spacer(1, 100))

    # Penalties
    story.append(Paragraph(
        "<b>Pénalités de retard :</b> En cas de retard de paiement et de versement des sommes dues par le Client au-delà des délais ci-dessus fixés, "
        "et après la date de paiement figurant sur la facture adressée à celui-ci, des pénalités de retard calculées au taux légal applicable au montant "
        "TTC du prix d'acquisition figurant sur ladite facture, seront acquises automatiquement et de plein droit au Prestataire, sans formalité aucune "
        "ni mise en demeure préalable.", styles["Normal"]
    ))

    # Build PDF
    doc.build(story)

    return f"facture_{year}_{month}.pdf"





def add_user():
    """
    email
    address
    amount
    TVA
    """
    if st.session_state["submitted"]:
        st.success("Utilisateur enregistré avec succès !")
        st.session_state["submitted"] = False  
        
    st.subheader("Pour ajouter un utilisateur veuillez compléter les informations suivantes : ")

    with open("users.json", "r") as f:
        users_data = json.load(f) 

    with st.form("user", clear_on_submit=True):
        email = st.text_input("Email : ")
        name = st.text_input("Nom de l'entreprise/association : ")
        address = st.text_input("Adresse : ")
        amount = st.number_input("Montant facturé par mois (€) :", min_value=0.0, step=0.1)
        tva = st.number_input("TVA (% ou laisser 0 si non applicable) : ", min_value=0.0, max_value=100.0, step=0.1)
        is_association = st.radio("Le destinateur est une :", ["Association", "Entreprise"], horizontal=True)
        submitted = st.form_submit_button("Enregistrer")

        if submitted:
            if not email:
                st.error("Merci d'entrer une adresse email valide.")
            else:
                users_data[email] = {"facture_number": 1, "name": name, "address": address, "amount": amount, "TVA": tva/100, "is_association": is_association}
                
                with open("users.json", "w") as f:
                    json.dump(users_data, f, indent=4)
                
                st.session_state["submitted"] = True
                st.rerun()


def send_email():

    if st.session_state["sent"]:
        st.success("Email envoyé avec succès !")
        st.session_state["sent"] = False  

    if "name" not in st.session_state:
        st.session_state.name = ""
    if "email" not in st.session_state:
        st.session_state.email = ""
    if "address" not in st.session_state:
        st.session_state.address = ""
    if "amount" not in st.session_state:
        st.session_state.amount = ""
    if "tva" not in st.session_state:
        st.session_state.tva = ""


    with open("users.json", "r") as f:
        users_data = json.load(f) 

    user_options = {users_data[user]["name"] : user for user in users_data.keys()} 
    selected_name = st.selectbox("Choisir un utilisateur :", list(user_options.keys()))
    selected_user = user_options[selected_name]

    st.session_state.facture_number = users_data[selected_user]["facture_number"]
    
    st.session_state.name = users_data[selected_user]["name"]
    st.session_state.email = selected_user
    st.session_state.address = users_data[selected_user]["address"]
    st.session_state.amount = users_data[selected_user]["amount"]
    st.session_state.tva = users_data[selected_user]["TVA"]
    st.session_state.assoc = users_data[selected_user]["is_association"]

    edit_mode = st.checkbox("Editer les données")

    if st.session_state["modified"]:
        st.success("Formulaire modifié avec succès !")
        st.session_state["modified"] = False  

    with st.form("info_form"):
        if edit_mode:
            email = st.text_input("Email : ", value=st.session_state.email)
            name = st.text_input("Nom de l'entreprise/association : ", value=st.session_state.name)
            address = st.text_input("Adresse : ", value=st.session_state.address)
            amount = st.number_input("Montant facturé par mois (€) :", min_value=0.0, step=0.1, value=float(st.session_state.amount))
            tva = st.number_input("TVA (% ou laisser 0 si non applicable) : ", min_value=0.0, max_value=100.0, step=0.1, value=float(st.session_state.tva*100.0))
            is_association = st.radio("Le destinateur est une :", ["Association", "Entreprise"], index=["Association", "Entreprise"].index(st.session_state.assoc), horizontal=True)
            facture_number = st.number_input("N° de la facture (auto incrémenté, ne toucher qu'en cas de problème !!)", min_value=1, step=1, value=st.session_state.facture_number)
            submitted = st.form_submit_button("Enregistrer")
        else:
            email = st.text_input("Email : ", value=st.session_state.email, disabled=True)
            name = st.text_input("Nom de l'entreprise/association : ", value=st.session_state.name, disabled=True)
            address = st.text_input("Adresse : ", value=st.session_state.address, disabled=True)
            amount = st.number_input("Montant facturé par mois (€) :", min_value=0.0, step=0.1, value=float(st.session_state.amount), disabled=True)
            tva = st.number_input("TVA (% ou laisser 0 si non applicable) : ", min_value=0.0, max_value=100.0, step=0.1, value=float(st.session_state.tva*100.0), disabled=True)
            is_association = st.radio("Le destinataire est une :", ["Association", "Entreprise"], index=["Association", "Entreprise"].index(st.session_state.assoc), horizontal=True, disabled=True)
            facture_number = st.number_input("N° de la facture (auto incrémenté, ne toucher qu'en cas de problème !!)", min_value=1, step=1, value=st.session_state.facture_number, disabled=True)
            submitted = st.form_submit_button("Enregistrer")
        
        if submitted and edit_mode:
            if not email:
                st.error("Merci d'entrer une adresse email valide.")
            else:
                if email != st.session_state.email:
                    users_data[email] = users_data.pop(st.session_state.email)

                users_data[email] = {"facture_number": facture_number, "name": name, "address": address, "amount": amount, "TVA": tva/100, "is_association": is_association}
                
                with open("users.json", "w") as f:
                    json.dump(users_data, f, indent=4)
                
                st.session_state["modified"] = True
                st.rerun()
    
    st.markdown("---")


    st.subheader("Quelques informations supplémentaires sont nécessaires : ")
    col1, col2, col3 = st.columns([1,1,1])

    with col1:
        is_paid = st.radio("La facture est :", ["Acquitée", "A payer"], horizontal=True)
    with col2:
        first_day = now.replace(day=1)
        formatted = first_day.strftime("%d/%m/%Y")
        edit_date = st.radio(f"La date d'émission {formatted} convient-elle ?", ["Oui", "Non"], horizontal=True)
    with col3:
        if edit_date == "Oui":
            emission_date = st.date_input("Choisir la date d'émission de la facture", value=date.today(), disabled=True)
            emission_date = formatted
        if edit_date == "Non":
            emission_date = st.date_input("Choisir la date d'émission de la facture", value=date.today()).strftime("%d/%m/%Y")


    col1, col2, col3, col4, col5, col6, col7 = st.columns([1]*7)
    with col4:
        edit_facture = st.button("Edition de la facture")
    
    if edit_facture:
        pdf_name = create_pdf(is_paid, facture_number, emission_date, name, address, email, is_association, amount, tva, now)
        
        users_data[email] = {"facture_number": facture_number+1, "name": name, "address": address, "amount": amount, "TVA": tva/100, "is_association": is_association}
        
        with open("users.json", "w") as f:
            json.dump(users_data, f, indent=4)

        col1, col2, col3 = st.columns([1, 2.5, 1])
        with col2:
            pdf_viewer(input="factures/"+pdf_name, width=700)
        
        st.session_state["created"] = True

    if st.button(f"Envoi de la facture à : {email}", disabled=(not st.session_state["created"]), use_container_width=True):
        pdf_name = "facture_2025_6.pdf"

        month_year = now.strftime("%m/%Y")
        try:
            msg = EmailMessage()
            msg["Subject"] = f"Facture {month_year}"
            msg["From"] = "no_reply@o2c.io"
            msg["To"] = email
            msg.set_content("This is a test email sent from Python.")

            with open("factures/" + pdf_name, "rb") as f:
                file_data = f.read()
                msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=pdf_name)

            smtp_server = "smtp.hostinger.com"
            smtp_port = 587

            your_email = "contact@o2c.io"
            your_password = "$t3xup3rYde53rt" 

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Start TLS encryption
                server.login(your_email, your_password)
                server.send_message(msg)
            
            st.session_state["sent"] = True


        except Exception as e:
            st.error(f"Failed to send email: {e}")


def remove_user():

    if st.session_state["removed"]:
        st.success("Formulaire modifié avec succès !")
        st.session_state["removed"] = False  

    with open("users.json", "r") as f:
        users_data = json.load(f) 

    st.write("Choisir un utilisateur à supprimer :")
    col1, col2 = st.columns([3,1])

    with col1:
        user_options = {users_data[user]["name"] : user for user in users_data.keys()} 
        selected_name = st.selectbox("fregb", list(user_options.keys()), label_visibility='collapsed')
        selected_user = user_options[selected_name]

    with col2:
        remove_but = st.button("Supprimer l'utilisateur", use_container_width=True)
        if remove_but:
            users_data.pop(selected_user)

            with open("users.json", "w") as f:
                json.dump(users_data, f, indent=4)
                
            st.session_state["removed"] = True
            st.rerun()


tab1, tab2, tab3 = st.tabs([
    "⌯⌲ Envoi d'une facture", 
    "➕ Ajout d'un utilisateur", 
    "➖ Suppression d'un utilisateur", 
])

with tab1:
    send_email()

with tab2:
    add_user()

with tab3:
    remove_user()
