
// add to basket
$(document).on('click', '#aside-menu-toggle-button', function (e) {
  e.preventDefault();
  $('#dashboard').toggleClass("has-aside-mobile-expanded")
})

$(document).on('click', '#burger', function (e) {
  e.preventDefault();
  $(this).toggleClass("is-active");
  $(".navbar-menu").toggleClass("is-active");
})

$(window).on('scroll', function() {
  window.getSelection().removeAllRanges();
});



$(document).ready(function () {
    // Get all menu items
    const menuItems = $('.menu-item');

    // Add click event listeners to menu items
    menuItems.on('click', function () {
        // Remove 'is-active' class from all menu items
        menuItems.removeClass('is-active');

        // Add 'is-active' class to the clicked menu item
        $(this).addClass('is-active');

        // Store the selected menu item in local storage
        localStorage.setItem('selectedMenuItem', $(this).data('item'));

        // Close the menu on menu item clicked event
        $('#dashboard').toggleClass("has-aside-mobile-expanded")
    });

    // Check local storage for a selected menu item and set its 'is-active' class
    const selectedMenuItem = localStorage.getItem('selectedMenuItem');
    if (selectedMenuItem) {
        const selectedItem = $(`[data-item="${selectedMenuItem}"]`);
        if (selectedItem.length) {
            selectedItem.addClass('is-active');
        }
    }
});


$(document).ready(function () {
  // Retrieve the active item from localStorage and set it initially
  const activeItem = localStorage.getItem("activeNavbarItem");
  if (activeItem) {
    const navbarItem = $(`.navbar-item[data-item="${activeItem}"]`);
    if (navbarItem.length) {
      navbarItem.addClass("is-active");
    }
  }

  // Toggle active class and update localStorage on navbar item click
  $(".navbar-item[data-item]").on('click',function () {
    // Remove active class from all items
    $(".navbar-item[data-item]").removeClass("is-active");

    // Add active class to the clicked item
    $(this).addClass("is-active");

    // Update localStorage with the clicked item
    localStorage.setItem("activeNavbarItem", $(this).data("item"));
  });
});

// Function to hide the loading spinner
function hideSpinner() {
  // Hide the preloader with a fade-out animation
  const preloader = document.getElementById('preloader');
  preloader.classList.add('fade-out');

  // Add a delay before removing the preloader (adjust the time as needed)
  setTimeout(() => {
    preloader.classList.remove('is-active');
  }, 400); // 400 milliseconds delay
}

// DOMContentLoaded can also be used
window.addEventListener('load', function () {
  hideSpinner()
});


document.addEventListener('DOMContentLoaded', () => {
  // Functions to open and close a modal
  function openModal($el) {
    $el.classList.add('is-active');
    document.documentElement.classList.add("is-clipped");
    console.log(document.documentElement.classList);
  }

  function closeModal($el) {
    $el.classList.remove('is-active');
    document.documentElement.classList.remove("is-clipped");
    console.log(document.documentElement.classList);
  }

  function closeAllModals() {
    (document.querySelectorAll('.modal') || []).forEach(($modal) => {
      closeModal($modal);
    });
  }

  // Add a click event on buttons to open a specific modal
  (document.querySelectorAll('.js-modal-trigger') || []).forEach(($trigger) => {
    const modal = $trigger.dataset.target;
    const $target = document.getElementById(modal);

    $trigger.addEventListener('click', () => {
      openModal($target);
    });
  });

  // Add a click event on various child elements to close the parent modal
  (document.querySelectorAll('.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .modal-cancel') || []).forEach(($close) => {
    const $target = $close.closest('.modal');

    $close.addEventListener('click', () => {
      closeModal($target);
    });
  });

  // Add a keyboard event to close all modals
  document.addEventListener('keydown', (event) => {
    if (event.code === 'Escape') {
      closeAllModals();
    }
  });
});

/// date and datatime with django flatpick 
// and flatpick js included in base file

function getFormattedISOString() {
  const now = new Date().toISOString(); // Ex: "2025-02-27T14:30:45.678Z"
  return now;
  //return now.replace("T", " ").split(".")[0]; // Ex: "2025-02-27 14:30:45"
}

function initFlatpickr() {
  console.log("htmx loed for dynamic jus of liedji first look");

  document.querySelectorAll(".datepickerinput").forEach((input) => {
    flatpickr(input, {
      enableTime: false,
      dateFormat: "Y-m-d",
    });
  });

  document.querySelectorAll(".datetimepickerinput").forEach((input) => {
    flatpickr(input, {
      enableTime: true,
      dateFormat: "Y-m-d H:i:S",
      //defaultDate: getFormattedISOString()  // Date actuelle
    });
  });
}

// Initialize Flatpickr on first page load
document.addEventListener("DOMContentLoaded", initFlatpickr);
document.addEventListener("htmx:afterOnLoad", function (event) {
  const dateInputs = event.target?.querySelectorAll(
    ".datepickerinput, .datetimepickerinput"
  );

  if (!dateInputs?.length) {
    // Clean up if calendar was created previously
    document
      .querySelectorAll(".flatpickr-calendar")
      .forEach((el) => el.remove());
    return;
  }

  dateInputs.forEach((input) => {
    if (input._flatpickr) return;

    flatpickr(input, {
      enableTime: input.classList.contains("datetimepickerinput"),
      dateFormat: input.classList.contains("datetimepickerinput")
        ? "Y-m-d H:i:S"
        : "Y-m-d",
      static: true,
      appendTo: input.parentElement,
    });
  });
});
