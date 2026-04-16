import type { Order, Customer } from '../types';

// jsPDF is loaded from a CDN in index.html, so we declare it here to satisfy TypeScript
declare const jspdf: any;

export const generatePdf = (order: Order, customer?: Customer) => {
    const { jsPDF } = jspdf;
    const doc = new jsPDF();

    const isProforma = order.status === 'Pending Payment';
    const title = isProforma ? 'Belabela Quarries Pro-forma Invoice' : 'Belabela Quarries Official Receipt';
    
    // Get customer details - use provided customer or fallback to order.customer (phone number)
    const customerName = customer?.name || 'N/A';
    const customerPhone = formatPhoneNumber(customer?.phone || order.customer || '');
    const numberOfItems = order.items.length;
    const transactionDisplay = order.transactionId || 'N/A';
    
    // Format payment method display
    const getPaymentMethodDisplay = () => {
        if (order.paymentMethod === 'card') return 'Credit/Debit Card';
        if (order.paymentMethod === 'eft') return 'EFT / Bank Transfer';
        if (order.paymentMethod === 'mobile_money') return 'Mobile Money';
        return order.paymentMethod || 'N/A';
    };
    
    const paymentMethodDisplay = getPaymentMethodDisplay();
    
    // Format payment status display
    const getPaymentStatusDisplay = () => {
        if (order.paymentStatus === 'paid') return 'Paid';
        if (order.paymentStatus === 'pending') return 'Pending';
        if (order.paymentStatus === 'failed') return 'Failed';
        return order.paymentStatus || 'Pending';
    };
    
    const paymentStatusDisplay = getPaymentStatusDisplay();
    
    // Format order status display
    const getOrderStatusDisplay = () => {
        if (order.status === 'Pending Payment') return 'Pending Payment';
        if (order.status === 'Processing') return 'Processing';
        if (order.status === 'Out for Delivery') return 'Out for Delivery';
        if (order.status === 'Delivered') return 'Delivered';
        if (order.status === 'Cancelled') return 'Cancelled';
        return order.status || 'Processing';
    };
    
    const orderStatusDisplay = getOrderStatusDisplay();
    
    const coordinates = `${order.deliveryLocation.lat.toFixed(6)}, ${order.deliveryLocation.lng.toFixed(6)}`;

    // Header
    doc.setFontSize(22);
    doc.setFont('helvetica', 'bold');
    doc.text(title, 105, 20, { align: 'center' });
    
    if (isProforma) {
        doc.setFontSize(10);
        doc.setTextColor(100);
        doc.text('This is not a tax invoice. Payment is required to process this order.', 105, 27, { align: 'center' });
    }

    // Order Details
    doc.setFontSize(12);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(0);
    doc.text(`Order ID: ${order.id}`, 20, 40);
    doc.text(`Date: ${new Date(order.date).toLocaleString()}`, 20, 47);
    doc.text(`Customer: ${customerName}`, 20, 54);
    doc.text(`Contact: ${customerPhone}`, 20, 61);

    // Delivery Details
    let yPos = 75;
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text('Delivery Address:', 20, yPos);
    
    doc.setFontSize(11);
    doc.setFont('helvetica', 'normal');
    yPos += 7;
    doc.text(order.deliveryLocation.address, 20, yPos, { maxWidth: 170 });
    yPos += 5;
    doc.text(`Coordinates: ${coordinates}`, 20, yPos);
    yPos += 5;

    if (order.distanceFromOrigin !== undefined) {
        doc.text(`Distance: ${order.distanceFromOrigin.toFixed(1)} km from Mmamashia`, 20, yPos);
        yPos += 5;
    }

    // Items Table Header
    yPos = Math.max(yPos, 95);
    doc.setTextColor(0);
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.text(`Item (${numberOfItems})`, 20, yPos);
    doc.text('Qty', 110, yPos);
    doc.text('Unit Price', 140, yPos);
    doc.text('Total', 175, yPos);
    doc.line(20, yPos + 3, 190, yPos + 3);
    yPos += 8;

    // Items Table Body
    doc.setFont('helvetica', 'normal');
    order.items.forEach(item => {
        // Handle long item names
        const itemName = item.product.name.length > 30 ? item.product.name.substring(0, 27) + '...' : item.product.name;
        doc.text(itemName, 20, yPos);
        doc.text(`${item.quantity} ${item.product.unit}`, 110, yPos);
        doc.text(`P${item.product.price.toFixed(2)}`, 140, yPos);
        doc.text(`P${(item.product.price * item.quantity).toFixed(2)}`, 175, yPos);
        yPos += 6;
        
        // Add new page if needed
        if (yPos > 270) {
            doc.addPage();
            yPos = 20;
        }
    });

    // Totals
    yPos += 5;
    doc.line(120, yPos, 190, yPos);
    yPos += 6;
    doc.setFont('helvetica', 'bold');
    doc.text('Subtotal:', 120, yPos);
    doc.text(`P${order.subtotal.toFixed(2)}`, 175, yPos);
    yPos += 6;
    doc.text('Delivery Fee:', 120, yPos);
    doc.text(order.deliveryFee === 0 ? 'Free' : `P${order.deliveryFee.toFixed(2)}`, 175, yPos);
    yPos += 6;
    doc.setFontSize(14);
    doc.text('Total:', 120, yPos);
    doc.text(`P${order.total.toFixed(2)}`, 175, yPos);

    // Payment Information - Clean formatting
    yPos += 12;
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.text('Payment Information:', 20, yPos);
    yPos += 6;
    doc.setFont('helvetica', 'normal');
    
    // Payment Method
    doc.text(`Method: ${paymentMethodDisplay}`, 20, yPos);
    yPos += 5;
    
    // Payment Status
    doc.text(`Payment Status: ${paymentStatusDisplay}`, 20, yPos);
    yPos += 5;
    
    // Order Status
    doc.text(`Order Status: ${orderStatusDisplay}`, 20, yPos);
    yPos += 5;
    
    // Transaction ID (if available)
    if (transactionDisplay !== 'N/A') {
        doc.text(`Transaction ID: ${transactionDisplay}`, 20, yPos);
        yPos += 5;
    }

    // Footer
    doc.setFontSize(9);
    doc.setTextColor(100);
    const footerY = doc.internal.pageSize.height - 20;
    doc.text('Belabela Quarries - Quality Construction Materials', 105, footerY, { align: 'center' });
    doc.text('+267 72 123 456 | info@belabelaquarries.co.bw', 105, footerY + 5, { align: 'center' });
    doc.text('Thank you for your business!', 105, footerY + 10, { align: 'center' });

    // Save PDF
    const filename = `Belabela-Quarries-${isProforma ? 'Proforma' : 'Receipt'}-${order.id.slice(0, 8)}.pdf`;
    doc.save(filename);
};

// Helper function to format phone number
const formatPhoneNumber = (phone: string) => {
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 8) {
        return `+267 ${cleaned}`;
    }
    return phone;
};