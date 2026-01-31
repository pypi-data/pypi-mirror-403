import streamlit as st

from xt_st_common.config import StreamlitBaseSettings

settings = StreamlitBaseSettings()


def page_header(
    page_title: str | None = None,
    page_logo: str | None = None,
    page_logo_width: int = 250,
    logout_url: str | None = None,
    header_border: bool = True,
    header_padding_top: str = "2rem",
):
    """
    Display the page header including Title, Logo, and optional Logout button.

    Args:
        page_title (str | None, optional): The title to show in the header. Defaults to None.
        page_logo (str | None, optional): A path to a page logo image. If not provided no page logo will be rendered.
            Defaults to None.
        page_logo_width (int, optional): The width of the page logo in the header. Defaults to 250.
        logout_url (str | None, optional): The logout url to be accessed when the logout button is pressed.
            If not provided the logout button will not be rendered. Defaults to None.
        header_border (bool, optional): Whether to render a single line border at the bottom of the header.
            Defaults to True.
        header_padding_top (str): adjust padding-top to move header up/down. Defaults to 2rem.
    """

    base_url = settings.STREAMLIT_SERVER_BASE_URL_PATH
    script_frame = st.empty()

    privacy_link = (
        f'<a id="privacy-link" class="btn-logout" href={settings.XT_PRIVACY_URL} target="_blank" >Privacy Policy</a>'
    )

    if logout_url is not None:
        # Load the css/icons for the button
        st.markdown(
            """
            <style scoped type="text/css">

            </style>
            """,
            unsafe_allow_html=True,
        )

        # Define the button
        logout_link = (
            f'<a id="logout-button" class="btn-logout" href={logout_url} role="button" target="_self" >🔐 Log out</a>'
        )
    else:
        logout_link = "&nbsp;"

    page_title = "" if page_title is None else f"<span class='app_title'>{page_title}</span>"

    page_logo = (
        ""
        if page_logo is None
        else f"<span class='app_logo'><img src='{page_logo}' width='{page_logo_width}px'></span>"
    )

    xt_logo = f"""<span class="xt_logo"><a href='{settings.XT_HOME_URL}'>
                <img src='{base_url}/app/static/media/XT_words_wrapped.png' width='200px'></a></span>"""

    # Display the page header including Title, Logo, and optional Logout button
    st.markdown(
        f"""
        <style scoped type="text/css">
            .main .block-container {{
                    padding-top: {header_padding_top};
            }}
            .xt_app_header {{
                {"border-bottom: 1px solid black;" if header_border else ""}
                width: 100%;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                row-gap: 10px;
            }}
            .app_logo_group{{
                display: flex;
                justify-content: flex-start;
                align-items: center;
                flex-wrap: nowrap;
            }}
            .app_title{{
                font-family: arial,sans-serif;
                font-size:200%;
                font-weight:700;
                color: #575757;
                white-space: nowrap;
                line-height: 2.5rem;
                align-self: flex-end;

            }}
            .app_logo_group::after {{
                font-family: sans-serif;
                font-size: small;
                content: '{settings.APP_TAG_TEXT}';
                display: inline-block;
                text-align: center;
                color: white;
                background-color: {settings.APP_TAG_BACKGROUND};
                border-radius: 30px;
                padding: 0px 15px;
                font-weight: bold;
                align-self: start;
            }}
            .xt_logo_group{{
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                row-gap: 10px;
            }}
            .xt_logo{{
            }}
            .btn-logout {{
                    box-shadow:inset 0px 1px 0px 0px #ffffff;
                    background:linear-gradient(to bottom, #f9f9f9 5%, #e9e9e9 100%);
                    background-color:#f9f9f9;
                    border-radius:6px;
                    border:1px solid #dcdcdc;
                    display:inline-block;
                    cursor:pointer;
                    color:#666666 !important;
                    font-family:Arial;
                    font-size:15px;
                    padding:4px 20px !important;
                    text-decoration:none;
                    text-shadow:0px 1px 0px #ffffff;
                    margin-right: 10px;
                    flex-grow: 1;
                    text-align: center;
                }}
                .btn-logout:hover {{
                    background:linear-gradient(to bottom, #e9e9e9 5%, #f9f9f9 100%);
                    background-color:#e9e9e9;
                }}
                .btn-logout:active {{
                    top:1px;
                }}
        </style>
        """
        + "<div class='xt_app_header'>"
        + "<div class='app_logo_group'>"
        + page_logo
        + page_title
        + "</div>"
        + "<div class='xt_logo_group'>"
        + privacy_link
        + logout_link
        + xt_logo
        + "</div>"
        + "</div>",
        unsafe_allow_html=True,
    )

    # Attach a function to clear the Cognito cookies when the logout button is clicked
    if settings.USE_COGNITO and len(settings.COGNITO_COOKIE) > 0:
        from streamlit_js_eval import streamlit_js_eval

        # Attach and onClick event handler to the logout button/link
        # When the user logs out the handler will remove cookies which are prefixed with
        # `settings.COGNITO_COOKIE`.
        # Also take the opportunity to have the signout button use the current window rather
        # than opening a new one.
        logout_script = (
            """
                var a = window.parent.document.getElementById("logout-button");
                a.onclick = function() {
                    all_cookies = Object.fromEntries(document.cookie.split("; ").map(c => c.split("=")))
                    cookie_list = Object.keys(all_cookies).filter(key => key.startsWith('"""
            + settings.COGNITO_COOKIE
            + """'))
                    cookie_list.forEach(e => {
                        window.parent.document.cookie = e+'=; expires=Thu, 01 Jan 1970 00:00:01 GMT'
                    })
                    return true;
                }
                // Override the target so that we reload the current page rather than opening a new one
                a.target = ""
            """
        )
        with script_frame:
            streamlit_js_eval(js_expressions=logout_script, key="js-logout-script")
