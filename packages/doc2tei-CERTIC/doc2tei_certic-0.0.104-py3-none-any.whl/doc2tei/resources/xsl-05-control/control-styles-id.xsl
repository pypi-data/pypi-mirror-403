<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
  xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
  xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"
  xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" 
  xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0" 
  xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0" 
  xmlns:math="http://www.w3.org/1998/Math/MathML" 
  xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0" 
  xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0" 
  xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0" 
  xmlns:ooo="http://openoffice.org/2004/office" 
  xmlns:ooow="http://openoffice.org/2004/writer" 
  xmlns:oooc="http://openoffice.org/2004/calc" 
  xmlns:dom="http://www.w3.org/2001/xml-events" 
  xmlns:xforms="http://www.w3.org/2002/xforms" 
  xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
  xmlns:rpt="http://openoffice.org/2005/report" 
  xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2" 
  xmlns:xhtml="http://www.w3.org/1999/xhtml" 
  xmlns:grddl="http://www.w3.org/2003/g/data-view#" 
  xmlns:officeooo="http://openoffice.org/2009/office" 
  xmlns:tableooo="http://openoffice.org/2009/table" 
  xmlns:drawooo="http://openoffice.org/2010/draw" 
  xmlns:calcext="urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0" 
  xmlns:loext="urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0" 
  xmlns:field="urn:openoffice:names:experimental:ooo-ms-interop:xmlns:field:1.0" 
  xmlns:formx="urn:openoffice:names:experimental:ooxml-odf-interop:xmlns:form:1.0" 
  xmlns:css3t="http://www.w3.org/TR/css3-text/"
  xmlns:xi="http://www.w3.org/2001/XInclude" 
  xmlns="http://www.tei-c.org/ns/1.0"
  exclude-result-prefixes="#all">
    
<xsl:output method="xml" encoding="UTF-8" indent="no"/>

<!-- ajouter LICENCE -->
<!-- voir README.md pour la description des traitements XSL -->
    
<xsl:template match="@*|node()">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>

<xsl:variable name="source">
    <xsl:value-of select="//*:application[starts-with(@ident,'circe')]/@ident"/>
</xsl:variable>    
    
<xsl:template match="*[ancestor::*:text]">
    <xsl:choose>
        <!-- TEI requires a wrapping <div> (body/figure is invalid) -->
        <xsl:when test="local-name()='body' and child::*[1][local-name()='figure']">
            <body>
                <xsl:copy-of select="@*"/>
                <div type="section1"><xsl:apply-templates/></div>
            </body>
        </xsl:when>
        <xsl:when test="contains(name(),'text:')">
            <xsl:choose>
                <xsl:when test="starts-with(@text:style-name,'TEI_local')">
                    <xsl:choose>
                        <xsl:when test="local-name()='p'">
                            <p>
                                <xsl:attribute name="rend" select="@text:style-name"/>
                                <xsl:apply-templates/>
                            </p>
                        </xsl:when>
                        <xsl:when test="local-name()='span'">
                            <hi>
                                <xsl:attribute name="rend" select="@text:style-name"/>
                                <xsl:apply-templates/>
                            </hi>
                        </xsl:when>
                        <xsl:otherwise>
                            <WARNING><xsl:text>Unable to deal with element styled "</xsl:text><xsl:value-of select="@text:style-name"/><xsl:text>".</xsl:text></WARNING>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:choose>
                        <xsl:when test="local-name()='p'">
                            <p>
                                <xsl:if test="$source='circe-Metopes'">
                                    <xsl:attribute name="rend">
                                        <xsl:value-of select="concat('unknownstyle:',@text:style-name)"/>
                                    </xsl:attribute>
                                </xsl:if>
                                <xsl:attribute name="xml:id">
                                    <xsl:text>p</xsl:text><xsl:number count="*[local-name()='p' and ancestor::*:body and not(parent::*:note) and not(parent::*:figure)]" from="*:body[not(parent::*:floatingText)]" level="any"/>
                                </xsl:attribute>
                                <WARNING><xsl:text>Unknown style "</xsl:text><xsl:value-of select="@text:style-name"/><xsl:text>" converted to p element. [#p</xsl:text><xsl:number count="*[local-name()='p']" from="*:body" level="any"/><xsl:text>]</xsl:text></WARNING>
                                <xsl:apply-templates/>
                            </p>
                        </xsl:when>
                        <xsl:when test="local-name()='span'">
                            <xsl:apply-templates/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:otherwise>
            </xsl:choose>      
        </xsl:when>
<!-- Suppression des éléments <hi> ne contenant que des espaces -->
        <xsl:when test="local-name()='hi' and matches(., '^\s*$')">
            <xsl:apply-templates/>
        </xsl:when>
        <xsl:when test="$source='circe-Metopes' and local-name()='graphic' and @url='../icono'">
            <graphic>
                <xsl:copy-of select="@* except(@url)"/>
                <xsl:attribute name="url"><xsl:text>Image should be linked</xsl:text></xsl:attribute>
            </graphic>
        </xsl:when>
        <xsl:when test="$source='circe-Metopes' and local-name()='graphic' and not(contains(@url, '/br/') or contains(@url, '/mr/') or contains(@url, '/hr/'))">
            <WARNING>
                <xsl:text>Iconographic resources are not properly organised.</xsl:text>
            </WARNING>
            <graphic>
                <xsl:copy-of select="@* except(@url)"/>
                <xsl:attribute name="url"><xsl:text>Iconographic resources are not properly organised.</xsl:text></xsl:attribute>
            </graphic>
        </xsl:when>
        <xsl:otherwise>
<!-- IDENTIFICATION DES ÉLÉMENTS 
à gérer : body/bibl, floatingText/* -->
            <xsl:choose>
                <xsl:when test="local-name()='math'">
                    <xsl:copy-of select="."/>
                </xsl:when>
                <xsl:when test="(./local-name()='div' and not(parent::*:front))
                            or (./local-name()='cit' and not(ancestor::*:cit) and not(ancestor::*:front)) 
                            or ./local-name()='figure' 
                            or (./local-name()='bibl')
                            or (./local-name()='p' and ancestor::*:body and not(parent::*:note) and not(parent::*:figure))
                            or (./local-name()='floatingText')
                            or ./local-name()='affiliation' or ./local-name()='email'">
                    <xsl:variable name="currentElementName">
                        <xsl:value-of select="name(.)"/>
                    </xsl:variable>
                    <xsl:element name="{$currentElementName}">
                        <xsl:copy-of select="@*"/>
                        <xsl:attribute name="xml:id">
                            <xsl:choose>
                                <xsl:when test="@xml:id">
                                    <xsl:copy-of select="@xml:id"/>
                                </xsl:when>
                                <xsl:when test="$currentElementName='affiliation'">
                                    <xsl:text>aff</xsl:text><xsl:number count="*[local-name()=$currentElementName]" from="*:front" level="any" format="01"/>
                                </xsl:when>
                                <xsl:when test="$currentElementName='email'">
                                    <xsl:text>email</xsl:text><xsl:number count="*[local-name()=$currentElementName]" from="*:front" level="any" format="01"/>
                                </xsl:when>
                                <xsl:when test="$currentElementName='figure'">
                                    <xsl:choose>
                                        <xsl:when test="parent::*:figure">
                                            <xsl:value-of select="$currentElementName"/><xsl:number count="*[local-name()=$currentElementName and not(parent::*:figure or parent::*:cell)]" from="*:text" level="any" format="01"/><xsl:text>_</xsl:text>
                                            <xsl:number count="*[local-name()=$currentElementName]" from="*:figure" level="single" format="1"/>
                                        </xsl:when>
                                        <xsl:when test="parent::*:cell">
                                            <xsl:value-of select="$currentElementName"/><xsl:number count="*[local-name()=$currentElementName and not(parent::*:figure or parent::*:cell)]" from="*:text" level="any" format="01"/><xsl:text>_</xsl:text>
                                            <xsl:number count="*:figure[parent::*:cell]" from="*:table" level="any" format="1"/>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <xsl:value-of select="$currentElementName"/><xsl:number count="*[local-name()=$currentElementName and not(parent::*:figure or parent::*:cell)]" from="*:text" level="any" format="01"/>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </xsl:when>
                                <xsl:when test="$currentElementName='bibl'">
                                    <xsl:value-of select="$currentElementName"/><xsl:number count="*[local-name()=$currentElementName]" from="*:text" level="any" format="001"/>
                                </xsl:when>
                                <xsl:when test="($currentElementName='div' and ./@type='bibliography') or ($currentElementName='div' and ./@type='appendix')">
                                    <xsl:value-of select="@type"/>
                                </xsl:when>
                                <xsl:when test="($currentElementName='div' and ./@type='review')">
                                    <xsl:text>review</xsl:text><xsl:value-of select="count(preceding::*:div[@type='review'])+1"/>
                                </xsl:when>
                                <xsl:when test="$currentElementName='floatingText'">
                                    <xsl:value-of select="$currentElementName"/><xsl:number count="*[local-name()=$currentElementName]" from="*:text" level="any"/>
                                </xsl:when>
                                <xsl:when test="ancestor::*:floatingText">
                                    <xsl:text>floatingText</xsl:text><xsl:value-of select="count(preceding::*:floatingText)+1"/><xsl:value-of select="$currentElementName"/><xsl:number count="*[local-name()=$currentElementName and ancestor::*:floatingText]" from="*:floatingText" level="any"/>
                                </xsl:when>
                                <xsl:when test="$currentElementName='p'">
                                    <xsl:value-of select="$currentElementName"/><xsl:number count="*[local-name()='p' and ancestor::*:body and not(parent::*:note) and not(parent::*:figure)]" from="*:body[not(parent::*:floatingText)]" level="any"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:value-of select="$currentElementName"/><xsl:number count="*[local-name()=$currentElementName]" from="*:body[not(parent::*:floatingText)]" level="any" format="01"/>
                                    <!-- [not(parent::*:note)] -->
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:attribute>
                        <xsl:apply-templates/>
                    </xsl:element>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:variable name="currentElementName">
                            <xsl:value-of select="name(.)"/>
                        </xsl:variable>
                        <xsl:element name="{$currentElementName}">
                            <xsl:copy-of select="@*"/>
                            <xsl:apply-templates/>
                        </xsl:element>
                    </xsl:otherwise>
            </xsl:choose>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
</xsl:stylesheet>