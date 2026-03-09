package com.caliclear.admin

import android.os.Bundle
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        val webView = WebView(this)
        setContentView(webView)
        
        // Configure WebView
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.allowFileAccess = true
        webView.settings.allowContentAccess = true
        webView.settings.loadWithOverviewMode = true
        webView.settings.useWideViewPort = true
        
        // Set WebViewClient to handle links in-app
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, url: String?): Boolean {
                // Load all URLs in the WebView
                view?.loadUrl(url ?: return true)
                return true
            }
        }
        
        // Load the admin panel URL
        // Change this to your deployed URL
        webView.loadUrl("https://g42vj5w4-5000.uks1.devtunnels.ms/admin.html")
    }
}
