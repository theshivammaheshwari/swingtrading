import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Support the Developer", page_icon="☕", layout="centered")

# Custom CSS
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div style='text-align: center; padding: 40px 20px; color: white;'>
        <h1>☕ Support the Developer</h1>
        <p style='font-size: 18px; margin-top: 20px;'>
            Thank you for considering support!<br>
            Your contribution helps keep this project running and ad-free.
        </p>
    </div>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_amount' not in st.session_state:
    st.session_state.selected_amount = None
if 'show_payment' not in st.session_state:
    st.session_state.show_payment = False

# Main container
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("---")
    st.markdown("### 💰 Choose Amount")
    
    # Preset amounts
    col_a, col_b = st.columns(2)
    
    with col_a:
        if st.button("☕ ₹100", use_container_width=True, type="secondary"):
            st.session_state.selected_amount = 10000
            st.session_state.show_payment = False
        
        if st.button("☕☕☕ ₹500", use_container_width=True, type="secondary"):
            st.session_state.selected_amount = 50000
            st.session_state.show_payment = False
    
    with col_b:
        if st.button("☕☕ ₹250", use_container_width=True, type="secondary"):
            st.session_state.selected_amount = 25000
            st.session_state.show_payment = False
        
        if st.button("🎁 ₹1000", use_container_width=True, type="secondary"):
            st.session_state.selected_amount = 100000
            st.session_state.show_payment = False
    
    st.markdown("---")
    
    # Custom amount
    st.markdown("### ✏️ Or Enter Custom Amount")
    custom_amount = st.number_input(
        "Amount in ₹",
        min_value=50,
        max_value=100000,
        value=100,
        step=50,
        help="Minimum ₹50, Maximum ₹1,00,000"
    )
    
    if st.button("Set Custom Amount", use_container_width=True, type="secondary"):
        st.session_state.selected_amount = custom_amount * 100  # Convert to paise
        st.session_state.show_payment = False
    
    st.markdown("---")
    
    # Show selected amount
    if st.session_state.selected_amount:
        amount_in_rupees = st.session_state.selected_amount / 100
        st.success(f"✅ Selected Amount: ₹{amount_in_rupees:.0f}")
        
        # Proceed button
        if st.button("💳 Proceed to Payment", use_container_width=True, type="primary"):
            st.session_state.show_payment = True
            st.rerun()
    else:
        st.info("👆 Please select or enter an amount above")
    
    # Show payment modal
    if st.session_state.show_payment and st.session_state.selected_amount:
        st.markdown("---")
        st.markdown("### 🔐 Processing Payment...")
        
        payment_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 20px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    text-align: center;
                }}
                .status {{
                    padding: 20px;
                    border-radius: 10px;
                    background: white;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .loader {{
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #FFDD00;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="status" id="status">
                <div class="loader"></div>
                <p style="color: #666; margin-top: 10px;">Opening Razorpay payment window...</p>
                <p style="color: #999; font-size: 12px;">Please don't close this page</p>
            </div>
            
            <script>
                console.log('Initializing payment...');
                
                var options = {{
                    "key": "rzp_live_WbMdjDSTBNEsE3",
                    "amount": {st.session_state.selected_amount},
                    "currency": "INR",
                    "name": "Swing Trading Dashboard",
                    "description": "Support the developer ☕",
                    "image": "https://cdn-icons-png.flaticon.com/512/3565/3565418.png",
                    "handler": function (response) {{
                        document.getElementById('status').innerHTML = 
                            '<h2 style="color: #2e7d32;">✅ Payment Successful!</h2>' +
                            '<p style="color: #666;">Thank you for your support!</p>' +
                            '<p style="color: #999; font-size: 14px;">Payment ID: ' + response.razorpay_payment_id + '</p>' +
                            '<button onclick="window.location.reload()" style="background: #FFDD00; color: #000; border: none; padding: 12px 24px; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 20px;">Make Another Payment</button>';
                        
                        // Send message to parent
                        window.parent.postMessage({{type: 'payment_success', id: response.razorpay_payment_id}}, '*');
                    }},
                    "prefill": {{
                        "email": "247shivam@gmail.com",
                        "contact": "+919468955596"
                    }},
                    "notes": {{
                        "amount": "₹{st.session_state.selected_amount / 100}",
                        "purpose": "Developer Support"
                    }},
                    "theme": {{
                        "color": "#FFDD00"
                    }},
                    "modal": {{
                        "ondismiss": function() {{
                            document.getElementById('status').innerHTML = 
                                '<h3 style="color: #f57c00;">⚠️ Payment Cancelled</h3>' +
                                '<p style="color: #666;">You cancelled the payment</p>' +
                                '<button onclick="window.location.reload()" style="background: #FFDD00; color: #000; border: none; padding: 12px 24px; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 20px;">Try Again</button>';
                            
                            // Send message to parent
                            window.parent.postMessage({{type: 'payment_cancelled'}}, '*');
                        }},
                        "escape": true,
                        "backdropclose": true
                    }}
                }};
                
                try {{
                    var rzp = new Razorpay(options);
                    
                    rzp.on('payment.failed', function (response) {{
                        document.getElementById('status').innerHTML = 
                            '<h3 style="color: #d32f2f;">❌ Payment Failed</h3>' +
                            '<p style="color: #666;">' + response.error.description + '</p>' +
                            '<p style="color: #999; font-size: 12px;">Reason: ' + response.error.reason + '</p>' +
                            '<button onclick="window.location.reload()" style="background: #FFDD00; color: #000; border: none; padding: 12px 24px; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 20px;">Try Again</button>';
                        
                        // Send message to parent
                        window.parent.postMessage({{type: 'payment_failed', error: response.error.description}}, '*');
                    }});
                    
                    // Open Razorpay modal automatically
                    setTimeout(function() {{
                        console.log('Opening Razorpay...');
                        rzp.open();
                    }}, 500);
                    
                }} catch(error) {{
                    console.error('Razorpay error:', error);
                    document.getElementById('status').innerHTML = 
                        '<h3 style="color: #d32f2f;">⚠️ Error</h3>' +
                        '<p style="color: #666;">Unable to load payment gateway</p>' +
                        '<p style="color: #999; font-size: 12px;">' + error.message + '</p>' +
                        '<button onclick="window.location.reload()" style="background: #FFDD00; color: #000; border: none; padding: 12px 24px; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 20px;">Reload Page</button>';
                }}
            </script>
        </body>
        </html>
        """
        
        # Render payment component
        components.html(payment_html, height=300, scrolling=False)
        
        # Back button
        if st.button("« Go Back", key="back_btn"):
            st.session_state.show_payment = False
            st.session_state.selected_amount = None
            st.rerun()

# Footer
st.markdown("---")
col_back1, col_back2, col_back3 = st.columns([1, 2, 1])
with col_back2:
    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        st.switch_page("app.py")  # Replace with your main app file name

st.markdown("""
    <div style='text-align: center; padding: 20px; color: white;'>
        <p style='font-size: 12px; opacity: 0.8;'>
            🔒 Secure payment powered by Razorpay<br>
            All transactions are encrypted and secure
        </p>
    </div>
""", unsafe_allow_html=True)