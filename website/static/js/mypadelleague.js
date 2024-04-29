document.addEventListener('DOMContentLoaded', function () {
    // Initialize Flatpickr
    flatpickr("#date_NonStop", {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
        time_24hr: true,
        minuteIncrement: 15,
        onChange: function(selectedDates, dateStr, instance) {
            // Check if the selected date is not empty
            if (selectedDates.length > 0) {
                // Get selected date and time
                const dateStart = new Date(selectedDates[0]);
                const dateEnd = new Date(dateStart.getTime() + 120 * 60000); // 120 minutes in milliseconds

                // Send an AJAX request to check for matches and update court visibility
                $.ajax({
                    type: 'POST',
                    url: '/checkMatches',
                    data: {
                        dateStart: dateStart.toISOString(),
                        dateEnd: dateEnd.toISOString()
                    },
                    success: function(response) {
                        // Update the court visibility based on the response
                        updateCourtVisibility(response);
                    },
                    error: function(error) {
                        console.log(error);
                    }
                });
            }

            // Additional code for your existing Flatpickr onChange logic
            const formContainer = document.getElementById('form-container');
            if (selectedDates.length > 0) {
                formContainer.style.display = 'block';
            } else {
                formContainer.style.display = 'none';
            }
        }
    });

    // Event listener for court number dropdown
    document.getElementById('court-number').addEventListener('change', function () {
        const selectedValue = parseInt(this.value);

        // Update court display
        updateCourtDisplay(selectedValue);

        // Update nonStop_duration dropdown based on court-number
        updateNonStopDurationDropdown(selectedValue);
    });

    // Event listener for court cards
    const courtElements = document.querySelectorAll('.Court');
    courtElements.forEach(court => {
        court.addEventListener('click', function () {
            const isAlreadySelected = court.classList.contains('selectedCourt');
            const selectedCourts = document.querySelectorAll('.selectedCourt');
            const selectedValue = parseInt(document.getElementById('court-number').value);

            if ((selectedCourts.length < selectedValue || isAlreadySelected) && !court.classList.contains('disabledCourt')) {
                court.classList.toggle('selectedCourt', !isAlreadySelected);

                // Update selected count label and total number of players
                updateSelectedCountLabel();
                updateTotalPlayers(selectedValue);
            } else {
                alert(`You can only select ${selectedValue} court(s).`);
            }
        });
    });

// Event listener for nonStop_duration dropdown
    document.getElementById('nonStop_duration').addEventListener('change', function () {
        const selectedValue = parseInt(this.value);
        const courtNumber = parseInt(document.getElementById('court-number').value);

        // Allow changing the value only if court-number is 2 or 3
        if (courtNumber === 2 || courtNumber === 3) {
            // Set default values 90 or 120 for court-number 2 or 3
            if (selectedValue !== 90 && selectedValue !== 120) {
                this.value = 90;
            }
        } else {
            // Set default value 120 for court-number 4 and disable changing
            this.value = 120;
        }
    });
});


// Function to update court display based on selected value
function updateCourtDisplay(selectedValue) {
    const courtElements = document.querySelectorAll('.Court');
    courtElements.forEach((court, index) => {
        court.classList.remove('selectedCourt', 'disabledCourt');
    });

    // Update selected count label and total number of players
    updateSelectedCountLabel();
    updateTotalPlayers(selectedValue);
}

// Function to update the selected count label
function updateSelectedCountLabel() {
    const selectedCourts = document.querySelectorAll('.selectedCourt');
    const selectedCountLabel = document.getElementById('selectedCountLabel');
    const selectedValue = parseInt(document.getElementById('court-number').value);

    if (selectedCourts.length > selectedValue) {
        selectedCourts.forEach(selectedCourt => {
            selectedCourt.classList.remove('selectedCourt');
        });

        alert(`You can only select ${selectedValue} court(s).`);
    }

    selectedCountLabel.textContent = `${selectedCourts.length} court${selectedCourts.length !== 1 ? 's' : ''} selected`;
}

// Function to update total number of players
function updateTotalPlayers(selectedValue) {
    const numPlayerTotal = document.getElementById('num_player_total');
    numPlayerTotal.value = selectedValue * 4;
}


// Function to update nonStop_duration dropdown based on court-number
function updateNonStopDurationDropdown(courtNumber) {
    const nonStopDurationDropdown = document.getElementById('nonStop_duration');

    // Set default values 90 or 120 for court-number 2 or 3
    // Set default value 120 and disable changing for court-number 4
    if (courtNumber === 2 || courtNumber === 3) {
        nonStopDurationDropdown.value = 90;
        nonStopDurationDropdown.removeAttribute('disabled');
    } else {
        nonStopDurationDropdown.value = 120;
        nonStopDurationDropdown.setAttribute('disabled', 'disabled');
    }
}

