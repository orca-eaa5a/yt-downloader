<template>
    <div class="full-screen">
        <div class="flex signup-pannel justify-content-end">
            <Button label="Sign Up" class="p-button-danger signup-button" />
        </div>
        <div class="s006">
            <form>
                <fieldset>
                    <div id='main-view'>
                        <legend>Download Youtube Video with<br>Fast Trimming</legend>
                        <legend style="opacity: 0">
                            <img class="p-4" src="@/assets/images/youtube_logo.png" style="width: 400px; height: 400px;" />
                        </legend>
                    </div>
                    <div class="inner-form fade-left-to-right">
                        <div>
                            <div class="p-inputgroup" id="searchbar">
                                <InputText placeholder="Input Youtube Video Link here" class="main-searchbar"/>
                                <Button icon="pi pi-search" class="p-button-danger"/>
                            </div>
                        </div>
                    </div>
                    <!--
                        TODO:
                        키워드 추천 목록
                    -->
                    <!-- <div class="suggestion-wrap">
                    <span>New Arrivals</span>
                    <span>Ladies</span>
                    <span>Mens</span>
                    <span>Accessories</span>
                    <span>Sale</span>
                    </div> -->
                </fieldset>
            </form>
        </div>
    </div>
</template>

<script>
export default {
    name: 'Main'
}
</script>

<style scoped lang='scss' >
@import "../assets/css/main.css";
@import "../assets/css/main-view.css";
@import "../assets/css/animation.css";

.p-button.p-button-danger{
    background:rgba(207,34,39,255);
    min-width: 60px;
}

.signup-button{
    padding: 10px;
    margin: 30px 30px 0px 0px;
    height: 40px;
    min-width: 100px !important;
    background-color: rgb(254, 114, 114) !important;
    border-radius: 20px;
}

.main-searchbar{
    font-size: 14pt;
    font-weight: 500;
}

.signup-pannel{
    min-width: 100vh;
    margin-bottom: 4rem;
}

// .p-inputgroup button:last-child{
//     border-top-right-radius: 34px !important;
//     border-bottom-right-radius: 34px !important;
// }
</style>
