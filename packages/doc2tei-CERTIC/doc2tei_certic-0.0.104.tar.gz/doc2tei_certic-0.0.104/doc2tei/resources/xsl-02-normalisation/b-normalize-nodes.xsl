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
  exclude-result-prefixes="">
    
<xsl:output method="xml" encoding="UTF-8" indent="no"/>

<!-- ajouter LICENCE -->
<!-- voir README.md pour la description des traitements XSL -->
    
<xsl:include href="b-normalize-nodes-index.xsl"/>
<xsl:include href="b-normalize-nodes-cit.xsl"/>
    
<xsl:variable name="source">
    <xsl:value-of select="//meta:user-defined[@meta:name='source']"/>
</xsl:variable> 
    
<xsl:template match="@*|node()">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()"/>
  </xsl:copy>
</xsl:template>
    
<!-- listes -->
<xsl:strip-space elements="*:list-item"/>
    
<xsl:template match="text:p[@text:style-name='List_20_Paragraph']">
    <xsl:choose>
        <xsl:when test="parent::text:list-item">
            <xsl:apply-templates/>
        </xsl:when>
        <xsl:otherwise>
            <text:p text:style-name="List_20_Paragraph">
                <xsl:apply-templates/>
            </text:p>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="text:list-item">
    <text:list-item>
        <xsl:copy-of select="@*"/>
        <xsl:copy-of select="child::text:p/@rendition"/>    
        <xsl:apply-templates/>
    </text:list-item>    
</xsl:template>  
    
<!-- ref croisées-->
<xsl:template match="text:bookmark-ref">
  <text:bookmark-ref text:ref-name="{@text:ref-name}">
    <xsl:apply-templates/>
  </text:bookmark-ref>
</xsl:template>
    
<!--
<xsl:template match="text:bookmark">
  <text:bookmark-ref text:ref-name="{@text:name}">
    <xsl:apply-templates/>
  </text:bookmark-ref>
</xsl:template>
    
-->
<!-- notes -->
<xsl:template match="text:note">
    <xsl:variable name="num">
        <xsl:value-of select="child::text:note-citation/node()"/>
    </xsl:variable>
    <xsl:copy>
        <xsl:apply-templates select="@*"/>
        <xsl:attribute name="text:num">
            <xsl:apply-templates select="$num"/>
        </xsl:attribute>
        <xsl:apply-templates/>
    </xsl:copy>
</xsl:template>
    
<xsl:template match="text:note-citation"/>
    
<xsl:template match="text:note-body">
    <xsl:apply-templates select="text:*|table:table"/>
</xsl:template>
    
<!-- enrichissements contenant tabulations : sont préservés mais les text:span sont segmentés autour des text:tab -->
<xsl:template match="text:span[descendant::text:tab]">
    <xsl:for-each-group select="node()" group-ending-with="text:tab">
        <text:span>
            <xsl:copy-of select="parent::text:span/@*"/>
            <xsl:apply-templates select="current-group()"/>
        </text:span>
    </xsl:for-each-group>

</xsl:template>

</xsl:stylesheet>