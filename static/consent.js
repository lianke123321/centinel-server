(function(){
    var consented = false;
    function Consent() {
        var consent_checkbox = document.getElementById("consent_checkbox")
        consent_checkbox.checked = false;
        consent_checkbox.addEventListener("click", function(){
            if(this.checked){
                consented = true;
            } else {
                consented = false;
            }
        });

        var form = document.getElementById("consent_form");
        form.onsubmit = function(event){
            if (!consented){
                alert("Please check the informed consent");
                return false
            }
        };
    };

    this.Consent = Consent;
})();