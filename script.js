// ============================================
// SECTION 1: Configuration & Constants
// ============================================

const CONFIG = {
    // API endpoint for Railway backend
    apiEndpoint: 'https://sunique-freight-api-production.up.railway.app/api/quote'
};

// ============================================
// SECTION 2: API Helper Function
// ============================================

async function getFreightQuote(formData) {
    const response = await fetch(CONFIG.apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
        body: JSON.stringify(formData)
    });
    
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Server error: ${response.status}`);
    }
    
    return await response.json();
}

// ============================================
// SECTION 3: Main Application
// ============================================

class ShippingQuoteApp {
    constructor() {
        this.currentStep = 0;
        this.progressSteps = [
            { id: 'validate', label: 'Validating Order', progress: 16 },
            { id: 'fetch', label: 'Fetching Products', progress: 33 },
            { id: 'dimensions', label: 'Calculating Dimensions', progress: 50 },
            { id: 'pallets', label: 'Optimizing Pallets', progress: 66 },
            { id: 'freight', label: 'Calculating Freight', progress: 83 },
            { id: 'quotes', label: 'Getting Quotes', progress: 100 }
        ];
    }
    
    async initialize() {
        try {
            console.log('Initializing application...');
            this.setupEventListeners();
            this.setDefaultPickupDate();
            console.log('Application initialized successfully');
        } catch (error) {
            console.error('Initialization error:', error);
            this.showError('Failed to initialize application. Please refresh the page.');
        }
    }
    
    setDefaultPickupDate() {
        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        const dateString = tomorrow.toISOString().split('T')[0];
        document.getElementById('pickupDate').value = dateString;
    }
    
    setupEventListeners() {
        document.getElementById('getQuoteBtn').addEventListener('click', () => {
            this.processQuote();
        });
        
        document.getElementById('newQuoteBtn').addEventListener('click', () => {
            this.resetForm();
        });
        
        document.getElementById('closeErrorModal').addEventListener('click', () => {
            this.hideError();
        });
        
        document.getElementById('closeErrorBtn').addEventListener('click', () => {
            this.hideError();
        });
        
        // Close modal on outside click
        document.getElementById('errorModal').addEventListener('click', (e) => {
            if (e.target.id === 'errorModal') {
                this.hideError();
            }
        });
    }
    
    async processQuote() {
        try {
            this.showProcessingSection();
            
            // Step 1: Validate input
            this.updateProgress(0, 'Validating input data...');
            const formData = this.validateAndGetFormData();
            await this.sleep(500);
            
            // Step 2-6: Call Netlify serverless function (all backend processing)
            this.updateProgress(1, 'Fetching order from inFlow...');
            await this.sleep(300);
            
            this.updateProgress(2, 'Calculating product dimensions...');
            await this.sleep(300);
            
            this.updateProgress(3, 'Optimizing pallet configuration...');
            await this.sleep(300);
            
            this.updateProgress(4, 'Calculating freight classes...');
            await this.sleep(300);
            
            this.updateProgress(5, 'Fetching shipping quotes from C.H. Robinson...');
            
            // Call the Netlify serverless function
            const result = await getFreightQuote(formData);
            
            // Display results
            await this.sleep(500);
            this.displayResults(result);
            
        } catch (error) {
            console.error('Quote processing error:', error);
            this.showError(error.message || 'An error occurred while processing your quote');
        }
    }
    
    validateAndGetFormData() {
        const orderNumber = document.getElementById('orderNumber').value.trim();
        const needsAssembly = document.getElementById('needsAssembly').checked ? 'yes' : 'no';
        const pickupZip = document.getElementById('pickupZip').value.trim();
        const destinationZip = document.getElementById('destinationZip').value.trim();
        const deliveryType = document.querySelector('input[name="deliveryType"]:checked').value;
        const liftgateService = document.getElementById('liftgateService').checked ? 'yes' : 'no';
        const pickupDateInput = document.getElementById('pickupDate').value;
        
        // Validations
        if (!orderNumber) throw new Error('Order number cannot be empty');
        if (!/^\d{5}$/.test(pickupZip)) throw new Error('Invalid pickup ZIP code. Must be 5 digits.');
        if (!/^\d{5}$/.test(destinationZip)) throw new Error('Invalid destination ZIP code. Must be 5 digits.');
        if (!pickupDateInput) throw new Error('Pickup date is required');
        
        // Format date to ISO format required by C.H. Robinson
        const date = new Date(pickupDateInput);
        const pickupDate = date.toISOString().split('T')[0] + 'T08:00:00';
        
        return {
            orderNumber,
            needsAssembly,
            pickupZip,
            destinationZip,
            deliveryType,
            liftgateService,
            pickupDate
        };
    }
    
    // UI Methods
    updateProgress(stepIndex, message) {
        const step = this.progressSteps[stepIndex];
        document.getElementById('progressPercentage').textContent = `${step.progress}%`;
        document.getElementById('progressFill').style.width = `${step.progress}%`;
        document.getElementById('progressMessage').textContent = message;
        
        // Update step markers
        document.querySelectorAll('.progress-step').forEach((el, idx) => {
            el.classList.remove('active', 'completed');
            if (idx < stepIndex) el.classList.add('completed');
            if (idx === stepIndex) el.classList.add('active');
        });
        
        // Update processing steps
        document.querySelectorAll('.processing-step').forEach((el, idx) => {
            el.classList.remove('active', 'completed');
            if (idx < stepIndex) {
                el.classList.add('completed');
                el.querySelector('i').className = 'fas fa-check-circle';
            } else if (idx === stepIndex) {
                el.classList.add('active');
                el.querySelector('i').className = 'fas fa-circle-notch fa-spin';
            } else {
                el.querySelector('i').className = 'fas fa-circle-notch fa-spin';
            }
        });
    }
    
    showProcessingSection() {
        document.getElementById('input-section').style.display = 'none';
        document.getElementById('processing-section').style.display = 'block';
        document.getElementById('results-section').style.display = 'none';
        
        // Reset progress
        this.updateProgress(0, 'Initializing...');
    }
    
    displayResults(data) {
        document.getElementById('processing-section').style.display = 'none';
        document.getElementById('results-section').style.display = 'block';
        
        // Populate order summary
        document.getElementById('resultOrderNumber').textContent = data.orderSummary.orderNumber;
        document.getElementById('resultTotalPallets').textContent = data.pallets.length;
        
        // Calculate total weight from pallets (includes pallet weight)
        const totalPalletWeight = data.pallets.reduce((sum, pallet) => sum + pallet.weight, 0);
        document.getElementById('resultTotalWeight').textContent = 
            `${Math.round(totalPalletWeight).toLocaleString()} lbs`;
        
        // Render pallets
        const palletsHtml = data.pallets.map((pallet, idx) => `
            <div class="pallet-card">
                <div class="pallet-header">
                    <span class="pallet-type">${pallet.palletType} Pallet #${idx + 1}</span>
                    <span class="pallet-class">Class ${pallet.freightClass}</span>
                </div>
                <div class="pallet-info">
                    <div><strong>Dimensions:</strong> ${pallet.length}×${pallet.width}×${pallet.height}"</div>
                    <div><strong>Weight:</strong> ${pallet.weight.toLocaleString()} lbs</div>
                    <div><strong>Type:</strong> ${pallet.palletType === 'Standard' ? '48×40' : '96×48'} pallet</div>
                </div>
            </div>
        `).join('');
        document.getElementById('palletResults').innerHTML = palletsHtml;
        
        // Render product details (only if element exists)
        const productDetailsElement = document.getElementById('productDetails');
        if (productDetailsElement) {
            const productsHtml = `
                <div class="product-row product-header">
                    <div>Product Name</div>
                    <div>Quantity</div>
                    <div>Dimensions</div>
                    <div>Weight (kg)</div>
                    <div>Weight (lb)</div>
                </div>
            ` + data.products.map(product => `
                <div class="product-row">
                    <div class="product-name">${product.name}</div>
                    <div>${product.quantity}</div>
                    <div>${product.length}×${product.width}×${product.height}"</div>
                    <div>${product.weight.toFixed(2)} kg</div>
                    <div>${(product.weight * 2.20462).toFixed(2)} lb</div>
                </div>
            `).join('');
            productDetailsElement.innerHTML = productsHtml;
        }
        
        // Render selected quote
        document.getElementById('resultCarrier').textContent = data.selectedQuote.carrier;
        document.getElementById('resultBaseRate').textContent = 
            `$${data.selectedQuote.baseRate.toFixed(2)}`;
        document.getElementById('resultMarkupPercent').textContent = 
            `${data.selectedQuote.markupPercentage.toFixed(0)}%`;
        document.getElementById('resultMarkup').textContent = 
            `$${data.selectedQuote.markup.toFixed(2)}`;
        document.getElementById('resultFinalQuote').textContent = 
            `$${data.selectedQuote.finalQuote.toFixed(2)}`;
        
        // Render all quotes
        const quotesHtml = data.quotes
            .sort((a, b) => a.totalCost - b.totalCost)
            .map((quote, idx) => {
                const isSelected = quote.carrier === data.selectedQuote.carrier;
                return `
                    <div class="quote-item ${isSelected ? 'selected' : ''}">
                        <div class="quote-item-header">
                            <div class="carrier-name">
                                ${isSelected ? '⭐ ' : ''}${quote.carrier}
                                ${isSelected ? ' (Selected)' : ''}
                            </div>
                            <div class="quote-cost">$${quote.totalCost.toFixed(2)}</div>
                        </div>
                        <div class="quote-item-details">
                            <span><strong>Service:</strong> ${quote.service}</span>
                            ${idx === 0 ? '<span style="color: #059669;">💰 Cheapest</span>' : ''}
                        </div>
                    </div>
                `;
            }).join('');
        document.getElementById('allQuotes').innerHTML = quotesHtml;
        
        // Scroll to top of results
        document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
    }
    
    showError(message) {
        document.getElementById('processing-section').style.display = 'none';
        document.getElementById('errorModal').classList.add('show');
        document.getElementById('errorMessage').textContent = message;
    }
    
    hideError() {
        document.getElementById('errorModal').classList.remove('show');
        document.getElementById('input-section').style.display = 'block';
    }
    
    resetForm() {
        document.getElementById('input-section').style.display = 'block';
        document.getElementById('results-section').style.display = 'none';
        document.getElementById('quoteForm').reset();
        this.setDefaultPickupDate();
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// ============================================
// SECTION 6: Application Initialization
// ============================================

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    const app = new ShippingQuoteApp();
    await app.initialize();
    console.log('Shipping Quote App initialized successfully');
});

