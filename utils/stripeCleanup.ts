// Utility to properly cleanup Stripe elements
export const cleanupStripeElements = () => {
    // Remove any Stripe iframes or elements
    const stripeElements = document.querySelectorAll('iframe[src*="stripe"]');
    stripeElements.forEach(element => {
      element.remove();
    });
    
    // Remove any Stripe modal overlays
    const stripeModals = document.querySelectorAll('[class*="Stripe"]');
    stripeModals.forEach(modal => {
      if (modal.parentNode) {
        modal.parentNode.removeChild(modal);
      }
    });
    
    // Remove any Stripe-related containers
    const stripeContainers = document.querySelectorAll('[class*="stripe"]');
    stripeContainers.forEach(container => {
      if (container.parentNode && container.parentNode !== document.body) {
        container.parentNode.removeChild(container);
      }
    });
  };
  
  // Cleanup on component unmount - export as function, not hook
  export const cleanupStripe = () => {
    return () => {
      cleanupStripeElements();
    };
  };