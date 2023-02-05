<template>
    <div class="full-screen">
        <div class="flex signup-pannel justify-content-end">
            <!-- <Button label="Sign Up" class="p-button-danger signup-button" /> -->
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
                            <div class="p-inputgroup">
                                <InputText placeholder="Input Youtube Video Link here" class="main-searchbar" v-model="this.videoLink" @:keyup="enterkey($event)"></InputText>
                                <InputText style="display: none;"></InputText>
                                <Button icon="pi pi-search" class="p-button-danger" v-on:click="queryYoutubeVideoInfo()"/>
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
    name: 'Main',
    methods:{
        queryYoutubeVideoInfo(){
            console.log(this.videoLink);
            this.$router.push('/search?q='+this.videoLink);
        },
        enterkey(evt) {
            if (evt.key === 'Enter') {
                this.queryYoutubeVideoInfo()
            }
        }
    },
    data(){
        return{
            videoLink: ''
        }
    },
    mounted(){
        document.body.style.zoom = "75%";
    }
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
