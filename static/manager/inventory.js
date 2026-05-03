const product = document.getElementsByName("product")[0];
const brandInput = document.getElementsByName('brand')[0];
const modelInput = document.getElementsByName('model')[0];
const specsInput = document.getElementsByName('specs')[0];
const weightInput = document.getElementsByName('weight')[0];
const priceInput = document.getElementsByName('price')[0];
const supplierInput = document.getElementsByName('supplier')[0];

function update() {
    const selectedOption = product.options[product.selectedIndex];
    const brand = selectedOption.getAttribute('data-brand');
    const model = selectedOption.getAttribute('data-model');
    const specs = selectedOption.getAttribute('data-specs');
    
    const weight = selectedOption.getAttribute('data-weight');
    const price = selectedOption.getAttribute('data-price');
    const supplier = selectedOption.getAttribute('data-supplier');

    brandInput.value = brand;
    modelInput.value = model;
    specsInput.value = specs;
    weightInput.value = weight;
    priceInput.value = price;
    supplierInput.value = supplier;
}

// // Run on change
product.addEventListener('change', update);

// Optional: run once on page load
window.onload = update;